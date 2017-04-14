import cachetools
import collections
import itertools
import pymongo
import bson
from .objectmodel import *
import PyQt5.QtCore as qtc


########################################################################################################################


class MongoQuery(MapObject):
    """Helper object for generating and saving Mongo query documents."""
    query = MapProperty(qtc.QVariant, '$query', default_set=lambda s: MapObject(parent=s))
    sort = MapProperty(qtc.QVariant, '$orderby', default_set=lambda s: MapObject(parent=s))

    def __init__(self, *args, query=None, sort=None, **kwargs):
        super().__init__(*args, **kwargs)

        if query is not None:
            self.query = MapObject(query)

        if sort is not None:
            self.sort = MapObject(sort)

    def requestedIds(self):
        """Returns a list of id's requested by the query. For example, for the query {'_id': 1234}, requestedIds
         would return [1234]."""
        idq = self.query.get('_id', None)

        if idq is None:
            return []
        elif isinstance(idq, bson.ObjectId):
            return [idq]
        elif isinstance(idq, collections.Mapping):
            return [i for i in itertools.chain(idq.get('$in', []),
                                               idq.get('$and', []),
                                               idq.get('$or', []))]

    @qtcore.pyqtSlot(str, qtcore.QVariant)
    def filterByValue(self, role_name, value):
        """Filter a role by a specific value."""
        self.query[role_name] = value

    @qtcore.pyqtSlot(str, result=qtcore.QVariant)
    def getFilterValue(self, role_name):
        """Return the value for a specific role's filter."""
        return self.query.get(role_name, None)


########################################################################################################################


class MongoObjectReference(MapObject):
    """Holds a reference to another object in the database."""

    referencedId = MapProperty(bson.ObjectId, 'referenced_id', default=None)
    referencedType = MapProperty(str, 'referenced_type', default='')

    autoLoadChanged = qtcore.pyqtSignal()
    autoLoad = MapProperty(bool, 'auto_load', notify=autoLoadChanged, default=False)

    readOnlyChanged = qtcore.pyqtSignal()
    readOnly = MapProperty(bool, 'read_only', notify=readOnlyChanged, default=False)

    def __init__(self, *args, item=None, **kwargs):
        """Initialize the object."""
        super().__init__(*args, **kwargs)
        self._item = None
        self.item = item

    itemChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(DocumentObject, notify=itemChanged)
    def item(self):
        """The referenced item."""
        return self._item

    @item.setter
    def item(self, item):
        """Sets the referenced item to item."""
        if item is not None:
            if not isinstance(item, MapObject):
                raise TypeError('Expected MapObject or subclass, got %s' % type(item))
            elif '_id' not in item:
                raise ValueError('Object does not have an _id: %s' % item)

            self._item = item
            self.referencedId = item['_id']
            self.referencedType = getattr(item, '_type', type(item).__name__)
        else:
            self._item = None
            self.referencedId = ''
            self.referencedType = ''


########################################################################################################################


class MongoObjectCursor(qtcore.QObject):
    """Automatically converts documents from a pymongo cursor to the appropriate subclass of
    MapObject. Also provides a few convenience methods, and the ability for use from within QML.
    """
    def __init__(self, cursor, database=None, default_type=None, **kwargs):
        """Initialize the cursor object. cursor is the (unused) pymongo cursor to wrap. New objects
        will be of type MapObject if their type can't be determined from their document's contents,
        unless an alternative is provided with default_type."""
        super().__init__(**kwargs)
        self._cursor = cursor
        self._database = database
        self._count = cursor.count()
        self._it = iter(cursor)
        self._default_type = default_type
        self._parent = kwargs.get('parent', None)
        self._done = False

    def __del__(self):
        """Automatically closes the cursor."""
        if self._cursor:
            self._cursor.close()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            doc = next(self._it)
            if doc is not None:
                obj = MapObject.from_document(MongoDatabase.unescaped(doc), default_type=self._default_type)
                if self._database is not None:
                    self._database._cache[doc['_id']] = doc
                    self._database.getAllReferencedObjects(obj)

                return obj
            else:
                return None

        except StopIteration:
            self._done = True
            raise

    def __len__(self):
        return self._count

    @qtcore.pyqtSlot(result=qtcore.QObject)
    def next(self):
        """Return the next object in the sequence, or None."""
        try:
            return self.__next__()
        except StopIteration:
            return None

    countChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(int, notify=countChanged)
    def count(self):
        """The number of documents in the cursor."""
        return self._count

    doneChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(bool)
    def done(self):
        """True if the cursor has been exhausted."""
        return self._done

    def close(self):
        """Closes the cursor."""
        self._cursor.close()
        self._cursor = None
        self._done = True


########################################################################################################################


class CursorObjectModel(ObjectModel):
    """A special version of ObjectModel that can fetch data from a MongoObjectCursor."""
    def __init__(self, _type, cursor, page_size=50, listen=True, parent=None):
        """Initialize the model. Loads the first 50 objects from the cursor."""
        super().__init__(_type=_type, listen=listen, parent=parent)

        self._cursor = cursor
        self._page_size = page_size
        self.fetchMore()

    @qtcore.pyqtSlot(result=bool)
    def canFetchMore(self, parent_idx=qtcore.QModelIndex()):
        """Return True if more objects can be loaded from the cursor."""
        return not self._cursor.done

    @qtcore.pyqtSlot()
    def fetchMore(self, parent_idx=qtcore.QModelIndex()):
        """Add another page of objects from the cursor to the model."""
        new = []
        for i in range(self._page_size):
            obj = self._cursor.next()
            if obj is None:
                break
            self._connect_to(obj)
            obj.setParent(self)
            new.append(obj)

        length = len(self)
        newlength = length + len(new)
        self.beginInsertRows(qtcore.QModelIndex(), length, newlength)
        self._original.extend(new)
        self._copy.extend(new)
        self.endInsertRows()


########################################################################################################################


class MongoDatabase(qtcore.QObject):
    """MongoDatabase provides integration between Mongo, Qt/QML, and qp."""

    @staticmethod
    def escaped(doc):
        """Return a new document, identical to doc except all reserved characters in dictionary keys are escaped
        with their unicode full-with variants."""
        MongoDatabase._escape_map = str.maketrans('$.', ''.join([chr(65284), chr(65294)]))
        return MongoDatabase._escaped(doc)

    @staticmethod
    def unescaped(doc):
        """Return a new document, identical to doc except all escaped characters in dictionary keys are restored
        to their original forms."""
        MongoDatabase._escape_map = str.maketrans(''.join([chr(65284), chr(65294)]), '$.')
        return MongoDatabase._escaped(doc)

    @staticmethod
    def _escaped(doc):
        if isinstance(doc, collections.Mapping):
            escaped = {}
            for key, value in doc.items():
                if isinstance(value, collections.Mapping) \
                        or (isinstance(value, collections.Sequence) and not isinstance(value, str)):
                    value = MongoDatabase._escaped(value)

                if isinstance(key, str):
                    key = key.translate(MongoDatabase._escape_map)

                escaped[key] = value
        elif isinstance(doc, collections.Sequence):
            escaped = []
            for item in doc:
                if isinstance(item, collections.Mapping) \
                        or (isinstance(item, collections.Sequence) and not isinstance(item, str)):
                    item = MongoDatabase._escaped(item)

                escaped.append(item)
        else:
            raise TypeError(type(doc))

        return escaped

    @staticmethod
    def _updates(obj):
        if isinstance(obj, ListObject):
            return MongoDatabase._listobject_updates(obj)
        elif isinstance(obj, MapObject):
            return MongoDatabase._mapobject_updates(obj)
        else:
            raise TypeError('%s is not a ListObject or MapObject.')

    @staticmethod
    def _listobject_updates(obj):
        """Build an update document from a ListObject."""
        response = {'$set': {}, '$unset': {}}

        original = obj.original

        if len(obj) < len(original):
            response['$set'].update({'': obj.document})
        else:
            for idx, item in enumerate(obj):
                if isinstance(item, DocumentObject):
                    if idx < len(original) and item is original[idx]:
                        updates = MongoDatabase._updates(item)
                        response['$set'].update({'%s.%s' % (idx, k): v for k, v in updates.get('$set', {}).items()})
                        response['$unset'].update({'%s.%s' % (idx, k): v for k, v in updates.get('$unset', {}).items()})
                    else:
                        response['$set'].update({str(idx): item.document})
                else:
                    if idx >= len(original) or item != original[idx]:
                        response['$set'].update({str(idx): item})

        if not response['$set']:
            del response['$set']

        if not response['$unset']:
            del response['$unset']

        return response

    @staticmethod
    def _mapobject_updates(obj):
        """Build an update document from a MapObject."""
        response = {'$set': {}, '$unset': {}}
        mods = obj.mods

        for key, value in obj.items():
            if key in mods:
                if isinstance(value, DocumentObject):
                    value = value.document

                response['$set'].update(MongoDatabase.escaped({key: value}))
            else:
                if isinstance(value, DocumentObject) and value.modified:
                    updates = MongoDatabase._updates(value)
                    response['$set'].update({('%s.%s' % (key, k)).rstrip('.'): v for k, v in updates.get('$set', {}).items()})
                    response['$unset'].update({'%s.%s' % (key, k): v for k, v in updates.get('$unset', {}).items()})

        for key in obj.dels:
            response['$unset'].update({key: None})

        if not response['$set']:
            del response['$set']

        if not response['$unset']:
            del response['$unset']

        return response

    def __init__(self, *args, uri=None, db=None, cache_size=100, **kwargs):
        """Initialize the database object."""
        super().__init__(*args, **kwargs)

        self._client = None
        self._db = None
        self._uri = ''
        self._collection_names = qtcore.QStringListModel(parent=self)
        self._status_message = ''
        self._error_msgs = []
        self._cache = cachetools.LFUCache(maxsize=cache_size)

    statusMessageChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(str, notify=statusMessageChanged)
    def statusMessage(self):
        """The current status message."""
        return self._status_message

    @statusMessage.setter
    def statusMessage(self, msg):
        self._status_message = str(msg)
        self.statusMessageChanged.emit()

    lastErrorsTextChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(str)
    def lastErrorsText(self):
        return '\n'.join(self._error_msgs)

    uriChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(str, notify=uriChanged)
    def uri(self):
        """The URI of the current database connection."""
        return self._uri

    collectionNamesChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(qtcore.QStringListModel, notify=collectionNamesChanged)
    def collectionNames(self):
        """A QStringListModel holding the names of the collections in the database."""
        return self._collection_names

    connectedChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(bool, notify=connectedChanged)
    def connected(self):
        """True if the object is currently connect to a database."""
        return self._db is not None

    @qtcore.pyqtSlot(str, str)
    def connect(self, dbname, uri=None):
        """Connect to a database at a given URI."""
        if self._client:
            self._client.close()

        if uri is None:
            uri = 'mongodb://localhost:27017/'

        self._client = pymongo.MongoClient(uri)
        self._db = self._client[dbname]

        self._uri = uri
        self.uriChanged.emit()

        self._collection_names.setStringList(self._db.collection_names())
        self.collectionNamesChanged.emit()

        self.statusMessage = 'Connected to database \'%s\' at %s' % (dbname, uri)
        self.connectedChanged.emit()

    @qtcore.pyqtSlot()
    def disconnect(self):
        """Disconnect from Mongo."""
        if self._client:
            self._client.close()
            self._db = None
            self._uri = ''
            self._collection_names.setStringList([])

            self._cache.clear()

            self.connectedChanged.emit()
            self.uriChanged.emit()
            self.collectionNamesChanged.emit()
            self.statusMessage = 'Disconnected from database.'

    @qtcore.pyqtSlot(str, MongoQuery, qtcore.QObject, result=MapObject)
    def getObject(self, _type, query=None, parent=None, use_cache=True):
        """Returns the first object matched by the query."""
        query = query if query is not None else MongoQuery()

        for i in query.requestedIds() if use_cache else []:
            doc = self._cache.get(i, None)
            if doc is not None:
                break
        else:
            _type = MapObject.subtype(_type)
            collection = self._db[_type.__collection__]
            doc = collection.find_one(query.query.document, modifiers={'$orderby': query.sort.document})

        return MapObject.from_document(doc, default_type=_type, parent=parent) if doc else None

    @qtcore.pyqtSlot(str, MongoQuery, qtcore.QObject, result=MongoObjectCursor)
    def getCursor(self, _type, query=None, parent=None):
        """Return a MongoObjectCursor resulting from the given query."""
        _type = MapObject.subtype(_type)
        query = query if query is not None else MongoQuery()
        collection = self._db[_type.__collection__]

        cursor = collection.find(query.query.document,
                                 modifiers={'$orderby': query.sort.document},
                                 no_cursor_timeout=True)

        return MongoObjectCursor(cursor, database=self, default_type=_type, parent=parent)

    @qtcore.pyqtSlot(str, MongoQuery, qtcore.QObject, result=ObjectModel)
    def getModel(self, _type, query=None, parent=None):
        """Return the results of a query in an ObjectModel."""
        _type = MapObject.subtype(_type)
        cursor = self.getCursor(_type, query)
        if cursor is not None:
            return CursorObjectModel(_type=_type, cursor=cursor, parent=parent)
        else:
            return None

    @qtcore.pyqtSlot(MapObject, result=bool)
    def saveObject(self, obj):
        """Save or update the object in the database."""
        collection = self._db[obj.__collection__]
        _id = obj.get('_id', None)

        if _id and obj.modified:
            updates = MongoDatabase._updates(obj)

            if '$set' in updates:
                updates['$set'] = MongoDatabase.escaped(updates['$set'])
            if '$unset' in updates:
                updates['$unset'] = MongoDatabase.escaped(updates['$set'])

            collection.update({'_id': obj['_id']}, updates, upsert=True)
        elif _id is None:
            doc = MongoDatabase.escaped(obj.document)
            result = collection.insert_one(doc)
            obj['_id'] = result.inserted_id

        obj.apply()
        self._cache[obj['_id']] = obj.document
        return True

    @qtcore.pyqtSlot(ObjectModel, result=bool)
    def saveModel(self, model):
        """Save all the objects in model."""
        self.statusMessage = 'Preparing to save %s objects...' % len(model)
        qtcore.QCoreApplication.processEvents()
        self._error_msgs, error_msgs = [], []

        # Sort the objects in the model by collection, ignoring unmodified objects
        objects = sorted(model, key=lambda o: o.__collection__)
        objects = filter(lambda o: o.modified or o.get('_id', None) is None, objects)

        # Perform a bulk operation for each collection
        for collection, group in itertools.groupby(objects, lambda o: o.__collection__):
            bulk = self._db[collection].initialize_unordered_bulk_op()

            # Save the list of objects so we can iterate over it twice
            group_list = list(group)

            # Inserts and updates
            for obj in group_list:
                _id = obj.get('_id', None)

                if _id is not None:
                    updates = MongoDatabase._updates(obj)
                    bulk.find({'_id': obj['_id']}).upsert().update(updates)
                else:
                    doc = MongoDatabase.escaped(obj.document)
                    bulk.insert(doc)

            # Perform the operation
            error_idxs = []
            try:
                result = bulk.execute()
            except pymongo.errors.InvalidOperation as e:
                pass
            except pymongo.errors.BulkWriteError as bwe:
                error_msgs.extend([e['errmsg'] for e in bwe.details['writeErrors']])
                error_idxs = [e['index'] for e in bwe.details['writeErrors']]

            # Cache and call apply() on objects that were saved successfully
            for i, o in enumerate(group_list):
                if i not in error_idxs:
                    self._cache[o['_id']] = o.document
                    o.apply()

        # If it's an ObjectModel, call deleteRemoved()
        if isinstance(model, ObjectModel):
            self.deleteRemoved(model)

        # Save any error messages
        self._error_msgs.extend(error_msgs)

        return not len(error_msgs)

    @qtcore.pyqtSlot(ObjectModel, result=bool)
    def deleteRemoved(self, model):
        """Delete all objects in the database that have been deleted from the model."""
        dels = model.deleted
        self.statusMessage = 'Preparing to delete %s objects...' % len(dels)
        qtcore.QCoreApplication.processEvents()

        objects = sorted(dels, key=lambda o: o.__collection__)
        for coll_name, group in itertools.groupby(objects, lambda o: o.__collection__):
            collection = self._db[coll_name]
            ids = list(set([o.get('_id', None) for o in group if o.get('_id', None) is not None]))
            collection.remove({'_id': {'$in': ids}})
            for i in ids:
                self._cache.pop(i, None)

        model.apply()
        return True

    @qtcore.pyqtSlot(MongoObjectReference, qtcore.QObject, result=MapObject)
    def getReferencedObject(self, ref, parent=None):
        """Loads an object into a MongoObjectReference."""
        obj = self.getObject(ref.referencedType, MongoQuery(query={'_id': ref.referencedId}), parent)
        ref.item = obj
        return obj

    @qtcore.pyqtSlot(MapObject, bool)
    def getAllReferencedObjects(self, obj, load_all=False):
        """Loads all of an object's references. If load_all is True, the reference's autoLoad property is ignored
        and the referenced object is loaded anyways."""
        for key, value in obj.items():
            if isinstance(value, MongoObjectReference) and (value.autoLoad or load_all):
                self.getReferencedObject(value, parent=obj)
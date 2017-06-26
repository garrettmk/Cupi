import collections
import itertools
import pymongo
import bson
from bson import ObjectId
from bson.json_util import dumps as json_dumps
from bson.codec_options import CodecOptions
from tzlocal import get_localzone
from .objects import *
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq


########################################################################################################################


class MongoQuery(MapObject):
    """Helper object for generating and saving Mongo query documents."""
    queryChanged = qtc.pyqtSignal()
    query = MapObjectProperty('$query', notify=queryChanged, default={})

    sortChanged = qtc.pyqtSignal()
    sort = MapObjectProperty('$orderby', notify=sortChanged, default={})

    @staticmethod
    def _clean(doc):
        """Remove any empty sub-documents from the query."""
        keys = list(doc.keys())

        for key in keys:
            value = doc[key]
            is_mapping = isinstance(value, collections.Mapping)
            is_list = isinstance(value, collections.Sequence) and not isinstance(value, str)

            if is_mapping or is_list \
                and len(value) == 0:
                del doc[key]

    @qtc.pyqtSlot(str, str, qtc.QVariant)
    def filterBy(self, role_name, filter_type, condition):
        """Filter a role using filter_type and condition."""
        if role_name is None:
            raise ValueError('role_name can not be None.')

        if filter_type == 'value':
            self.query[role_name] = condition
        elif filter_type == 'regex':
            self.query[role_name] = {'$regex': condition, '$options': 'i'}
        elif filter_type == 'range_min':
            priors = self.query.get(role_name, {})
            params = {'$gte': condition}
            priors.update(params)
            self.query[role_name] = priors
        elif filter_type == 'range_max':
            priors = self.query.get(role_name, {})
            params = {'$lte': condition}
            priors.update(params)
            self.query[role_name] = priors
        else:
            raise ValueError('Invalid filter type: ' + str(filter_type))

    @qtc.pyqtSlot(str, str, result=qtc.QVariant)
    def getFilter(self, role_name, filter_type):
        """Return the condition used to filter a given role."""
        if role_name is None:
            raise ValueError('role_name can not be None.')

        try:
            if filter_type == 'value':
                return self.query[role_name]
            elif filter_type == 'regex':
                return self.query[role_name]['$regex']
            elif filter_type == 'range_min':
                return self.query[role_name]['$gte']
            elif filter_type == 'range_max':
                return self.query[role_name]['$lte']
            else:
                raise ValueError('Invalid filter type: ' + str(filter_type))
        except KeyError:
            return None

    @qtc.pyqtSlot(str)
    def deleteFilter(self, role_name):
        """Delete the filter for a given role."""
        if role_name is None:
            raise ValueError('role_name can not be None.')

        try:
            del self.query[role_name]
            self._clean(self.query)
        except KeyError:
            pass


    @qtc.pyqtSlot(str, int)
    def sortBy(self, role_name, order):
        """Sort the results by role, in ascending or descending order."""
        if order == qtc.Qt.AscendingOrder:
            self.sort[role_name] = pymongo.ASCENDING
        elif order == qtc.Qt.DescendingOrder:
            self.sort[role_name] = pymongo.DESCENDING
        else:
            raise ValueError('Invalid sort order: ' + str(order))


    @qtc.pyqtSlot(str, result=qtc.QVariant)
    def getSortOrder(self, role_name):
        """Return the role used to sort query results."""
        if role_name is None:
            raise ValueError('role_name can not be None.')

        try:
            order = self.sort[role_name]
        except KeyError:
            return None

        if order == pymongo.ASCENDING:
            return qtc.Qt.AscendingOrder
        elif order == pymongo.DESCENDING:
            return qtc.Qt.DescendingOrder
        else:
            return order


########################################################################################################################


class MongoObjectCursor(qtc.QObject):
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
                    self._database.getAllReferencedObjects(obj)

                return obj
            else:
                return None

        except StopIteration:
            self._done = True
            self.doneChanged.emit()
            raise

    def __len__(self):
        return self._count

    @qtc.pyqtSlot(result=qtc.QObject)
    def next(self):
        """Return the next object in the sequence, or None."""
        try:
            return self.__next__()
        except StopIteration:
            return None

    countChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(int, notify=countChanged)
    def count(self):
        """The number of documents in the cursor."""
        return self._count

    doneChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(bool)
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

    @qtc.pyqtSlot(result=bool)
    def canFetchMore(self, parent_idx=qtc.QModelIndex()):
        """Return True if more objects can be loaded from the cursor."""
        return not self._cursor.done

    @qtc.pyqtSlot()
    def fetchMore(self, parent_idx=qtc.QModelIndex()):
        """Add another page of objects from the cursor to the model."""
        length = len(self)
        new_length = min(length + self._page_size, self.totalRows())
        new_objects = [next(self._cursor) for i in range(new_length - length)]
        if not new_objects:
            return

        self.beginInsertRows(qtc.QModelIndex(), length, new_length - 1)
        self._original.extend(new_objects)
        self._current.extend(new_objects)
        self.endInsertRows()

    @qtc.pyqtSlot(result=int)
    def totalRows(self):
        try:
            return self._cursor.count
        except AttributeError:
            return 0


########################################################################################################################


class MongoDatabase(qtc.QObject):
    """MongoDatabase provides integration between Mongo, Qt/QML, and qp."""

    @staticmethod
    def escaped(doc):
        """Return a new document, identical to doc except all reserved characters in dictionary keys are escaped
        with their unicode full-with variants."""
        escape_map = str.maketrans('$.', ''.join(['\uFF04', '\uFF0E']))
        return MongoDatabase._escaped(doc, escape_map)

    @staticmethod
    def unescaped(doc):
        """Return a new document, identical to doc except all escaped characters in dictionary keys are restored
        to their original forms."""
        escape_map = str.maketrans(''.join(['\uFF04', '\uFF0E']), '$.')
        return MongoDatabase._escaped(doc, escape_map)

    @staticmethod
    def _escaped(doc, escape_map):
        doc_is_string = isinstance(doc, str)
        doc_is_map = isinstance(doc, collections.Mapping)
        doc_is_sequence = isinstance(doc, collections.Sequence) and not doc_is_string

        # If doc is a map, escape its keys and any sub-documents
        if doc_is_map:
            escaped_doc = {}
            for key, value in doc.items():
                key = key.translate(escape_map)
                value = MongoDatabase._escaped(value, escape_map)
                escaped_doc[key] = value
            return escaped_doc

        # If doc is a sequence, escape any sub-documents
        elif doc_is_sequence:
            escaped_doc = []
            for item in doc:
                item = MongoDatabase._escaped(item, escape_map)
                escaped_doc.append(item)
            return escaped_doc

        # All other values just get returned
        else:
            return doc


    @staticmethod
    def _updates(obj):
        is_obj_model = isinstance(obj, ObjectModel)
        is_map_obj = isinstance(obj, MapObject)

        if is_obj_model:
            return MongoDatabase._objectmodel_updates(obj)
        elif is_map_obj:
            return MongoDatabase._mapobject_updates(obj)
        else:
            raise TypeError('%s is not a MapObject or ObjectModel.')

    @staticmethod
    def _objectmodel_updates(model):
        """Build an update document from an ObjectModel."""
        response = {'$set': {}, '$unset': {}}
        original = model.original_document

        # If the new list is shorter than the original, just re-write the list
        if len(model) < len(original):
            response['$set'].update({'': model.current_document})

        # If the new list is the same length or longer than the original, check each item
        else:
            for idx, obj in enumerate(model):
                # If this item was in the original, add its updates
                if idx < len(original) and obj is original[idx]:
                    # Get this object's update doc
                    obj_updates = MongoDatabase._updates(obj)

                    # Format the $set and $unset fields
                    obj_sets = {'%s.%s' % (idx, k): v for k, v in obj_updates.get('$set', {}).items()}
                    obj_unsets = {'%s.%s' % (idx, k): v for k, v in obj_updates.get('$unset', {}).items()}

                    # Add these to the response document
                    response['$set'].update(obj_sets)
                    response['$unset'].update(obj_unsets)

                # This item was not in the original at this index, so write the whole object document
                else:
                    response['$set'].update({str(idx): obj.current_document})

        # Clean up the response document
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
                if isinstance(value, (collections.Mapping, collections.Sequence)) \
                        and not isinstance(value, str):
                    value = MongoDatabase.escaped(value)

                response['$set'].update({MongoDatabase.escaped(key): value})
            else:
                if isinstance(value, DocumentObject) and value.modified:
                    updates = MongoDatabase._updates(value)
                    response['$set'].update({('%s.%s' % (MongoDatabase.escaped(key), k)).rstrip('.'): v for k, v in updates.get('$set', {}).items()})
                    response['$unset'].update({'%s.%s' % (MongoDatabase.escaped(key), k): v for k, v in updates.get('$unset', {}).items()})

        for key in obj.dels:
            response['$unset'].update({key: None})

        if not response['$set']:
            del response['$set']

        if not response['$unset']:
            del response['$unset']

        return response

    def __init__(self, *args, uri=None, db=None, maxsize=100, **kwargs):
        """Initialize the database object."""
        super().__init__(*args, **kwargs)

        self._client = None
        self._db = None
        self._uri = ''
        self._collection_names = []
        self._status_message = ''
        self._error_msgs = []

    statusMessageChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(str, notify=statusMessageChanged)
    def statusMessage(self):
        """The current status message."""
        return self._status_message

    @statusMessage.setter
    def statusMessage(self, msg):
        self._status_message = str(msg)
        self.statusMessageChanged.emit()

    lastErrorsTextChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(str)
    def lastErrorsText(self):
        return '\n'.join(self._error_msgs)

    uriChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(str, notify=uriChanged)
    def uri(self):
        """The URI of the current database connection."""
        return self._uri

    collectionNamesChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(qtc.QVariant, notify=collectionNamesChanged)
    def collectionNames(self):
        """A QStringListModel holding the names of the collections in the database."""
        return self._collection_names

    connectedChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(bool, notify=connectedChanged)
    def connected(self):
        """True if the object is currently connect to a database."""
        return self._db is not None

    @qtc.pyqtSlot(str, str)
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

        self._collection_names = self._db.collection_names()
        self.collectionNamesChanged.emit()

        self.statusMessage = 'Connected to database \'%s\' at %s' % (dbname, uri)
        self.connectedChanged.emit()

    @qtc.pyqtSlot()
    def disconnect(self):
        """Disconnect from Mongo."""
        if self._client:
            self._client.close()
            self._db = None
            self._uri = ''
            self._collection_names = []

            self.connectedChanged.emit()
            self.uriChanged.emit()
            self.collectionNamesChanged.emit()
            self.statusMessage = 'Disconnected from database.'

    @qtc.pyqtSlot(str, MongoQuery, qtc.QObject, result=MapObject)
    def getObject(self, _type, query=None, parent=None):
        """Returns the first object matched by the query."""
        _type = MapObject._subclass(_type)
        collection = self._db[_type.__collection__].with_options(codec_options=CodecOptions(tz_aware=True,
                                                                                            tzinfo=get_localzone()))

        query, sort = (query.query.current_document, query.sort.current_document) if query is not None else ({}, {})
        query['_type'] = {'$in': [_type.__name__] + _type._all_subclass_names()}

        doc = collection.find_one(query, modifiers={'$orderby': sort})
        obj = MapObject.from_document(doc, default_type=_type, parent=parent) if doc else None
        if obj is not None:
            self.getAllReferencedObjects(obj)

        return obj

    @qtc.pyqtSlot(str, MongoQuery, qtc.QObject, result=MongoObjectCursor)
    def getCursor(self, _type, query=None, parent=None):
        """Return a MongoObjectCursor resulting from the given query."""
        _type = MapObject._subclass(_type)
        collection = self._db[_type.__collection__].with_options(codec_options=CodecOptions(tz_aware=True,
                                                                                            tzinfo=get_localzone()))

        query, sort = (query.query.current_document, query.sort.current_document) if query is not None else ({}, {})
        query['_type'] = {'$in': [_type.__name__] + _type._all_subclass_names()}

        cursor = collection.find(query, modifiers={'$orderby': sort}, no_cursor_timeout=True)

        return MongoObjectCursor(cursor, database=self, default_type=_type, parent=parent)

    @qtc.pyqtSlot(str, MongoQuery, qtc.QObject, result=ObjectModel)
    def getModel(self, _type, query=None, parent=None, **kwargs):
        """Return the results of a query in an ObjectModel."""
        _type = MapObject._subclass(_type)
        cursor = self.getCursor(_type, query)
        if cursor is not None:
            return CursorObjectModel(_type=_type, cursor=cursor, parent=parent, **kwargs)
        else:
            return None

    @qtc.pyqtSlot(MapObject, result=bool)
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
            doc = MongoDatabase.escaped(obj.current_document)
            result = collection.insert_one(doc)
            obj['_id'] = result.inserted_id

        obj.apply()
        return True

    @qtc.pyqtSlot(ObjectModel, result=bool)
    def saveModel(self, model):
        """Save all the objects in model."""
        self.statusMessage = 'Preparing to save %s objects...' % len(model)
        qtc.QCoreApplication.processEvents()

        self._error_msgs, error_msgs = [], []
        count = 0

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
                count += 1
                self.statusMessage = 'Scanning object %s' % count
                qtc.QCoreApplication.processEvents()

                _id = obj.get('_id', None)

                if _id is not None:
                    updates = MongoDatabase._updates(obj)
                    bulk.find({'_id': obj['_id']}).upsert().update(updates)
                else:
                    doc = MongoDatabase.escaped(obj.current_document)
                    bulk.insert(doc)
                    obj.id = doc['_id']

            # Perform the operation
            self.statusMessage = 'Performing bulk update...'
            qtc.QCoreApplication.processEvents()
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
                    o.apply()

        # If it's an ObjectModel, call deleteRemoved()
        if isinstance(model, ObjectModel):
            self.deleteRemoved(model)

        # Save any error messages
        self._error_msgs.extend(error_msgs)

        self.statusMessage = 'Save operation completed with %s errors.' % len(self._error_msgs)
        return not len(self._error_msgs)

    @qtc.pyqtSlot(ObjectModel, result=bool)
    def deleteRemoved(self, model):
        """Delete all objects in the database that have been deleted from the model."""
        dels = model.deleted
        self.statusMessage = 'Deleting %s objects...' % len(dels)
        qtc.QCoreApplication.processEvents()

        objects = sorted(dels, key=lambda o: o.__collection__)
        for coll_name, group in itertools.groupby(objects, lambda o: o.__collection__):
            collection = self._db[coll_name]
            ids = list(set([o.get('_id', None) for o in group if o.get('_id', None) is not None]))
            collection.remove({'_id': {'$in': ids}})

        model.apply()
        self.statusMessage = 'Done.'
        return True

    @qtc.pyqtSlot(MapObjectReference, qtc.QObject, result=MapObject)
    def getReferencedObject(self, ref, parent=None):
        """Loads an object into a MongoObjectReference."""
        obj = self.getObject(ref.referencedType or type(ref).referencedType,
                             MongoQuery(query={'_id': ref.referencedId}),
                             parent=parent)

        ref.ref = obj
        return obj

    @qtc.pyqtSlot(MapObject, bool)
    def getAllReferencedObjects(self, obj, load_all=False, _already_loaded=None):
        """Loads all of an object's references. If load_all is True, the reference's autoLoad property will be
        ignored and the referenced object will be loaded anyways."""
        already_loaded = _already_loaded if _already_loaded is not None else {}

        if isinstance(obj, collections.Mapping):
            items = obj.values()
        elif isinstance(obj, collections.Sequence):
            items = obj
        else:
            raise TypeError('Expected mapping or sequence, got %s' % type(obj))

        for item in items:
            if isinstance(item, MapObjectReference) and (item.autoLoad or load_all):
                try:
                    item.ref = already_loaded[item.referencedId]
                except KeyError:
                    self.getReferencedObject(item, parent=item)
                    already_loaded[item.referencedId] = item.ref
                    #self.getAllReferencedObjects(item.ref, False, already_loaded)

            elif isinstance(item, (collections.Mapping, collections.Sequence)) \
                    and not isinstance(item, str):
                self.getAllReferencedObjects(item, load_all, already_loaded)

    @qtc.pyqtSlot(ObjectModel, bool)
    def saveReferencedObjects(self, refs_model):
        """Save the objects references by an iterable of MongoObjectReferences."""
        objs = [ref.ref for ref in refs_model if ref.ref is not None]
        return self.saveModel(objs)

    @qtc.pyqtSlot(str, str, result=str)
    def getQueryText(self, collection, query):
        """Returns the formatted text of the documents return by query."""
        try:
            collection = self._db[collection]
            cursor = collection.find(eval(query), modifiers={'$maxScan': 50})
            result = '\n\n'.join([json_dumps(doc, indent=4) for doc in cursor])
            return result
        except Exception as e:
            return repr(e)

    @qtc.pyqtSlot(str, MongoQuery, result=int)
    def queryCount(self, _type, query):
        """Returns the number of documents in the given query."""
        cursor = self.getCursor(_type, query)
        return cursor.count



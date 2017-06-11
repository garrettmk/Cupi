import abc, collections, datetime, itertools, sip, types
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq
from bson.json_util import dumps as json_dumps
#from .objectmodel import ObjectModel

########################################################################################################################


class CupiObjectMetaclass(sip.wrappertype, abc.ABCMeta):
    """A QObject-compatible metaclass """


########################################################################################################################


class MapObjectMetaclass(sip.wrappertype, abc.ABCMeta):
    """
    A QObject-compatible metaclass for MapObject.

    When loading MapObject-derived classes from JSON documents, it is necessary to look up a subclass by name. Also,
    when an ObjectModel is created for a certain type, it must look at that types attributes and determine which ones
    are pyqtProperty's. Because these are lengthy operations that must be done frequently, MapObjectMetaclass keeps
    track of the information and makes it available.

    subclasses:         A dictionary relating class names to their types.
    map_properties:     A dictionary relating class names to a list of property names (the pyqtProperty attributes of
                        the class)
    """
    subclasses = {}
    properties = {}

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = args[0]
        MapObjectMetaclass.subclasses[name] = cls
        MapObjectMetaclass.properties[name] = [name for name in dir(cls) if isinstance(getattr(cls, name), qtc.pyqtProperty)]


########################################################################################################################


class MapObject(qtc.QObject, collections.MutableMapping, metaclass=MapObjectMetaclass):
    """
    The primary purpose of MapObject is to provide property access to a dictionary of key/value pairs.
    It supports the DocumentObject interface, tracks changes and signals on modification.

    MapObject inherits from collections.MutableMapping, and can be used as a dictionary. Key/value pairs can be
    accessed from QML by either using getValue()/setValue(), or by declaring properties using MapProperty().
    """

    qml_major_version = 1
    qml_minor_version = 0

    @staticmethod
    def from_document(document, default_type=None, **kwargs):
        """Creates a MapObject subclass from a document. If the appropriate subclass can't be determined from the
        document contents, default_type is used. If no default_type is provided, the object will be a MapObject.
        Any remaining arguments (such as parent) are passed on to the new object's constructor."""
        _type = document.get('_type', None)
        object_type = MapObjectMetaclass.subclasses.get(_type, None) \
                        or default_type \
                        or MapObject

        return object_type(document, **kwargs)

    @staticmethod
    def _subclass(_type):
        """Return the subclass represented by _type, if _type is a string. If _type is a class, it is checked to be
        a subclass of MapObject before being returned. If _type is a string that does not represent a subclass of
        MapObject, ValueError is raised. If _type is a not a subclass of MapObject, TypeError is raised."""
        if isinstance(_type, str):
            try:
                return MapObjectMetaclass.subclasses[_type]
            except KeyError:
                raise ValueError('%s is not a valid subclass of MapObject.' % _type)
        elif issubclass(_type, MapObject):
            return _type
        else:
            raise TypeError('%s is not a subclass of MapObject.' % _type)

    @classmethod
    def _all_subclass_names(cls):
        """Returns a list with the names of all of this classes' subclasses."""
        return [c.__name__ for c in cls.__subclasses__()] + [g for s in cls.__subclasses__() \
                                                             for g in s._all_subclass_names()]

    @staticmethod
    def register_subclasses():
        """Automatically registers all subclasses with the QML engine."""
        for name, _type in MapObjectMetaclass.subclasses.items():
            qtq.qmlRegisterType(_type,
                                name,
                                getattr(_type, 'qml_major_version', 1),
                                getattr(_type, 'qml_minor_version', 0),
                                name)

    def __init__(self, *args, **kwargs):
        """Initialize the MapObject. If the parent argument is provided, it is passed to the QObject constructor.
        All other arguments are used to set the initial state of the map."""

        # Creating an object from QML passes (None,) as constructor arguments. Get rid of this so it doesn't
        # mess up the dict constructor down the line.
        if args == (None,):
            args = ()

        # Filter out keyword arguments that match declared property names
        prop_kwargs = {kw: value for kw, value in kwargs.items() if kw in MapObjectMetaclass.properties[type(self).__name__]}
        kwargs = {kw: value for kw, value in kwargs.items() if kw not in prop_kwargs}

        # Call the parent constructors
        super().__init__(parent=kwargs.pop('parent', None))

        # Initialize members
        self._map = dict(*args, **kwargs)
        for val in self._map.values():
            self._connect(val)

        self._mods = dict()
        self._dels = set()
        self._modified = False

        _type = type(self)
        if '_type' not in self and _type is not MapObject:
            self._map['_type'] = _type.__name__

        # Initialize properties
        for prop, value in prop_kwargs.items():
            setattr(self, prop, value)

    def _connect(self, obj):
        """Utility function, sets the parent and connects to obj's change signals."""
        if isinstance(obj, (MapObject, ObjectModel)):
            obj.setParent(self)
            obj.modifiedChanged.connect(self.modifiedChanged)

    def _disconnect(self, obj):
        """Utility function, removes self as obj's parent and disconnects from obj's change signals."""
        if isinstance(obj, (MapObject, ObjectModel)):
            obj.setParent(None)
            obj.modifiedChanged.disconnect(self.modifiedChanged)

    @qtc.pyqtSlot(str, result=qtc.QVariant)
    def getValue(self, key, **kwargs):
        """Returns the value for a given key. Besides the key, there are two optional keyword arguments: default
        and default_set. If default is provided, its value is returned if the map does not contain the key. If
        default is callable, it is called with the instance of MapObject as its argument, and its return value is
        used instead.
        default_set is similar to default, except that its value (or the value it returns, if it is callable) is
        assigned to key in the map before it is returned.
        If neither default nor default_set are provided, and the key is not found in the map, KeyError is raised.
        """
        try:
            value = self[key]
            enforce_type = kwargs.get('enforce_type', None)
            if enforce_type is not None and type(value) is not enforce_type:
                convert = kwargs.get('convert_type', None)
                value = convert(self, value) if convert else enforce_type(value)
                self[key] = value
            return value
        except KeyError as e:
            if 'default_set' in kwargs:
                default = kwargs['default_set']
                default = default(self) if callable(default) else default
                self[key] = default
                return default
            elif 'default' in kwargs:
                default = kwargs['default']
                default = default(self) if callable(default) else default
                return default
            else:
                raise e

    @qtc.pyqtSlot(str, qtc.QVariant)
    def setValue(self, key, value, *args):
        """Assigns value to key in the map. Any additional arguments are assumed to be notification signals, and
        their emit() attribute is called."""
        self[key] = value.toVariant() if isinstance(value, qtq.QJSValue) else value
        for arg in args:
            arg.emit()

    def __getitem__(self, key):
        """Retrieve value from the map. KeyError is raised if the provided key does not exist in the map."""
        if key in self._mods:
            return self._mods[key]
        elif key in self._dels:
            raise KeyError(key)
        elif key in self._map:
            return self._map[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        """Assign a value to a key."""
        was_modified = self._modified

        if key not in self._map \
                or not self._map[key] is value:
            # It's a new key, or a modification of the original key's value
            self._disconnect(self._map.get(key, None))
            self._disconnect(self._mods.get(key, None))
            self._mods[key] = value
        else:
            # We are setting a key back to its original value
            self._disconnect(self._mods.pop(key, None))

        self._connect(value)

        # If this key was marked as deleted, clear it
        self._dels.discard(key)

        # If modification status changed, emit the signal
        if self.modified != was_modified:
            self.modifiedChanged.emit()

    def __delitem__(self, key):
        """Delete a key-value pair."""
        was_modified = self._modified

        if key in self._dels:
            raise KeyError(key)
        elif key in self._mods:
            self._disconnect(self._mods.pop(key, None))
        elif key in self._map:
            self._disconnect(self._map[key])
        else:
            raise KeyError(key)

        self._dels.add(key)

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    def __iter__(self):
        """Return an iterator for the map's keys."""
        return itertools.chain(filter(lambda k: k not in self._dels, self._map.keys()),
                               filter(lambda k: k not in self._map, self._mods.keys()))

    def __len__(self):
        """Return the number of keys in the map."""
        return sum(1 for k in iter(self))

    def keys(self):
        """Return an iterator of the map's keys."""
        return iter(self)

    def items(self):
        """Yields the key-value pairs in the document."""
        for key in self:
            yield key, self[key]

    def values(self):
        """Yields the values in the document."""
        for key in self:
            yield self[key]

    def update(self, *args, **kwargs):
        """Checks if the first argument is a QJSValue before passing on to super()."""
        if len(args) == 1 and isinstance(args[0], qtq.QJSValue):
            args[0] = args[0].toVariant()

        super().update(*args, **kwargs)

    @property
    def map(self):
        """Returns a read-only view (a MappingProxyType) of the last 'saved' version of the map."""
        return types.MappingProxyType(self._map)

    @property
    def mods(self):
        """Returns a read-only view (a MappingProxyType) of document's unsaved modifications."""
        return types.MappingProxyType(self._mods)

    @property
    def dels(self):
        """Returns a tuple of keys that have been deleted from the document since the last save."""
        return tuple(self._dels)

    modifiedChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(bool, notify=modifiedChanged)
    def modified(self):
        """True if the document has been modified since the last save."""
        if self._mods or self._dels:
            self._modified = True
            return True

        for item in self.values():
            if isinstance(item, (MapObject, ObjectModel)) and item.modified:
                self._modified = True
                return True

        self._modified = False
        return False

    @qtc.pyqtSlot()
    def apply(self):
        """Saves changes in this document and all sub-documents."""
        was_modified = self._modified
        self._modified = None

        new = {}
        for key, item in self.items():
            if isinstance(item, (MapObject, ObjectModel)):
                item.apply()

            new[key] = item

        self._map = new
        self._mods.clear()
        self._dels.clear()

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtc.pyqtSlot()
    def revert(self):
        """Discards any changes in this document and all sub-documents since they were last saved."""
        was_modified = self._modified
        self._modified = None

        for key, value in self._map.items():
            if isinstance(value, (MapObject, ObjectModel)):
                value.revert()

        self._mods.clear()
        self._dels.clear()

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @property
    def document(self):
        response = {}

        for key, value in self.items():
            if isinstance(value, (MapObject, ObjectModel)):
                response[key] = value.document
            else:
                response[key] = value

        return response

    @qtc.pyqtSlot(result=str)
    def getDocumentText(self):
        """Returns the object's document property as a formatted block of text."""
        return json_dumps(self.document, indent=4)

    idChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(qtc.QVariant, notify=idChanged)
    def id(self):
        """Returns the object's ID."""
        return self.getValue('_id', default=None)

    @id.setter
    def id(self, value):
        """Set the object's id."""
        had_id = self.hasId
        self.setValue('_id', value, self.idChanged)
        if self.hasId != had_id:
            self.hasIdChanged.emit()

    hasIdChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(bool, notify=hasIdChanged)
    def hasId(self):
        """Returns True if this object has been assigned an id."""
        return '_id' in self


########################################################################################################################


def Property(type, key, fget=None, fset=None, read_only=False, **kwargs):
    """Creates a property that uses MapObject's getValue() and setValue() functions as getter and setter. Supports
    defaults and notification signals. MapProperty() is a convenience wrapper for pyqtProperty().

    Arguments:
        type                    The type of the property.
        key                     The key assigned to this property.
        notify                  (optional) The notification signal assigned to this property.
        default, default_set    (optional) Passed on to MapObject.getValue()
        read_only               Sets a property to read-only

    Usage:  class PropertyMap(MapObject):
                onXChanged = pyqtSignal()
                x = MapProperty(str, 'x', notify=onXChanged, default='n/a')

    """
    fget_kwargs = {k:v for k, v in kwargs.items() if k in ['default', 'default_set', 'enforce_type', 'convert_type']}
    fset_kwargs = {k:v for k, v in kwargs.items() if k in ['enforce_type']}
    kwargs = {k: v for k, v in kwargs.items() if (k not in fget_kwargs and k not in fset_kwargs)}

    fget = fget or (lambda self: MapObject.getValue(self, key, **fget_kwargs))

    if 'notify' in kwargs:
        fset = fset or (lambda self, value: MapObject.setValue(self, key, value, kwargs['notify'].__get__(self)))
    else:
        fset = fset or (lambda self, value: MapObject.setValue(self, key, value))

    if read_only:
        fset = None

    return qtc.pyqtProperty(type, fget=fget, fset=fset, **kwargs)


########################################################################################################################


def MapObjectProperty(_type, key, **kwargs):
    """Convenience function for creating MapObject properties."""
    kwargs.pop('default', None)
    default_set = kwargs.get('default_set', None)
    default_set = default_set if default_set is not None else lambda self: _type(parent=self)
    convert_type = lambda self, value: _type(value, parent=self)

    return Property(_type, key, enforce_type=_type, convert_type=convert_type, default_set=default_set, **kwargs)


########################################################################################################################


def ListProperty(key, **kwargs):
    """Convenience function for creating ListObject properties."""
    kwargs.pop('default', None)
    kwargs.pop('fget', None)

    default_set = kwargs.get('default_set', None)
    default_set = default_set if default_set is not None else lambda self: list()
    convert_type = lambda self, value: list(value)

    return Property(qtc.QVariant, key, enforce_type=list, convert_type=convert_type, default_set=default_set, **kwargs)


########################################################################################################################


def DateTimeProperty(key, **kwargs):
    """Convenience function for create datetime/QDateTime properties."""
    kwargs.pop('default', None)
    kwargs.pop('fget', None)

    default_set = kwargs.get('default_set', None)
    default_set = default_set if default_set is not None else lambda self: datetime.datetime.fromtimestamp(0, datetime.timezone.utc)
    convert_type = lambda self, value: datetime.datetime.fromtimestamp(value.toSecsSinceEpoch(), datetime.timezone.utc)

    return Property(qtc.QDateTime,
                    key,
                    enforce_type=datetime.datetime,
                    convert_type=convert_type,
                    default_set=default_set,
                    **kwargs)


########################################################################################################################


class MapObjectReferenceMetaclass(MapObjectMetaclass):

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ref_type = args[2]['referent_type']
        if ref_type == MapObject.__name__:
            return

        props = MapObjectMetaclass.properties[ref_type]

        for name in props:
            if name in dir(cls):
                continue

            fset = lambda self, value, n=name: setattr(self.ref, n, value)
            fget = lambda self, n=name: getattr(self.ref, n)
            setattr(cls, name + 'Changed', qtc.pyqtSignal())
            setattr(cls, name, qtc.pyqtProperty(qtc.QVariant, fget=fget, fset=fset))


########################################################################################################################


class MapObjectReference(MapObject, metaclass=MapObjectReferenceMetaclass):
    """Holds a reference to another object in the database."""
    referent_type = 'MapObject'

    referentId = Property(qtc.QVariant, 'referent_id', default=None)
    referentType = Property(str, 'referent_type', default=referent_type)

    autoLoadChanged = qtc.pyqtSignal()
    autoLoad = Property(bool, 'auto_load', notify=autoLoadChanged, default=False)

    def __init__(self, *args, **kwargs):
        """Initialize the object."""
        self._ref = None
        super().__init__(*args, **kwargs)

    refChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(MapObject, notify=refChanged)
    def ref(self):
        """The referenced item."""
        return self._ref

    @ref.setter
    def ref(self, item):
        """Sets the referenced item to item."""
        if item is not None:
            if not isinstance(item, MapObject):
                raise TypeError('Expected MapObject or subclass, got %s' % type(item))

            self._ref = item
            self.referentId = item.id
            self.referentType = getattr(item, '_type', type(item).__name__)
        else:
            self._ref = None
            self.referentId = None
            self.referentType = 'MapObject'

########################################################################################################################


class ObjectModelMetaclass(sip.wrappertype, abc.ABCMeta):
    """A QObject-compatible metaclass for ObjectModel."""


########################################################################################################################


class ObjectModel(qtc.QAbstractItemModel, collections.MutableSequence, metaclass=ObjectModelMetaclass):
    """ObjectModel provides a QAbstractItemModel interface to a list of qp.MapObject objects. It will automatically
    provide 'role' names based on the object types properties, and can be used as either a list or a table model.
    It also implements the collections.MutableSequence interface, so it can be used as a Python list as well.
    """

    def __init__(self, _type, ref_type=None, objects=None, listen=True, parent=None):
        """Initializes the model. _type is a qp.Object subclass, which will be used to determine the role names
        the model provides. objects is the list of objects to use. If listen is True (the default) the model will
        connect to any property change signals the object type provides, and will translate those to dataChanged
        signals.
        """
        super().__init__(parent=parent)

        self._original = list(objects) if objects is not None else []
        self._current = list(self._original)
        self._removed = list()

        # Take ownership of content objects
        for obj in self._original:
            obj.setParent(self)

        # The type of object stored by the model
        self._type = MapObject._subclass(_type)

        # If self._type is a kind of ObjectReference, self._ref_type is the type of object stored by the reference
        # If ref_type is not provided, try to determine the type by asking reference type
        if issubclass(self._type, MapObjectReference):
            if ref_type is not None:
                self._ref_type = MapObject._subclass(ref_type)
            else:
                try:
                    self._ref_type = MapObject._subclass(self._type.referencedType)
                except (AttributeError, ValueError, TypeError):
                    raise TypeError('A valid reference type could not be determined.')
        else:
            self._ref_type = None

        # Discover property names for content and referenced objects and assign role numbers
        props = MapObjectMetaclass.properties[self._type.__name__]
        self._role_to_prop = {r: p for r, p in enumerate(props, qtc.Qt.UserRole)}

        if self._ref_type is not None:
            props = MapObjectMetaclass.properties[self._ref_type.__name__]
            self._ref_role_to_prop = {r: p for r, p in enumerate(props, max(self._role_to_prop) + 1)}
        else:
            self._ref_role_to_prop = {}

        # Set the default column names
        self._column_to_role = {}
        self._column_names = []
        self.setColumns()

        # Connect to property change signals
        self._listen = listen
        if listen:
            for obj in self:
                self._connect_to(obj)

        # self.modified gets called so often that storing the modification state helps improve performance
        self._modified = None
        self.modified

    def __getitem__(self, index):
        """Retrieve the object at the given index."""
        return self._current[index]

    def __setitem__(self, index, item):
        """Replace the object at the given index."""
        was_modified = self._modified
        self._modified = None

        # Disconnect from the object currently in the list
        current = self[index]
        self._disconnect_from(current)
        if current.parent() is self:
            current.setParent(None)

        # Replace the item in the list
        self._current[index] = item
        item.setParent(self)
        if self._listen:
            self._connect_to(item)

        # Emit change signals
        if self.modified != was_modified:
            self.modifiedChanged.emit()
            topleft = self.createIndex(index, 0)
            bottomright = self.createIndex(index, len(self._column_to_role))
            self.dataChanged.emit(topleft, bottomright)

    def __delitem__(self, row):
        """Remove an object from the model."""
        self.removeRows(row, 1)

    def __len__(self):
        """Return the number of objects in the model."""
        return len(self._current)

    def __iter__(self):
        """Return an iterator for the model."""
        return iter(self._current)

    @qtc.pyqtSlot(int, result=MapObject)
    def getObject(self, index):
        """Convenience function for accessing objects by index from QML."""
        return self[index]

    @qtc.pyqtSlot(int, MapObject)
    def setObject(self, index, obj):
        """Convenience function for assigning objects by index from QML."""
        self[index] = obj

    @qtc.pyqtSlot(int, int, result=bool)
    def removeRows(self, row, count, parent=qtc.QModelIndex()):
        """Starting at :row:, remove :count: rows from the model."""
        was_modified = self._modified
        self._modified = None

        # Signal any attached views that we are about to change the model
        self.beginRemoveRows(parent, row, row + count - 1)

        # Remove the objects from the model
        for i in range(count):
            obj = self[row]
            self._disconnect_from(obj)
            if obj.parent() is self:
                obj.setParent(None)

            del self._current[row]
            self._removed.append(obj)

        # Emit change signals
        if self.modified != was_modified:
            self.modifiedChanged.emit()

        # Signal attached views that we are done changing the model
        self.endRemoveRows()

        return True

    @qtc.pyqtSlot(int, result=bool)
    def removeRow(self, row, parent=qtc.QModelIndex()):
        """Remove the object at the given row from the model."""
        return self.removeRows(row, 1, parent)

    @qtc.pyqtSlot(result=int)
    def length(self):
        """Convenience function, returns the number of objects in the model."""
        return len(self)

    @qtc.pyqtSlot(qtc.QObject)
    def append(self, item):
        """Append an object to the end of the model."""
        collections.MutableSequence.append(self, item)

    @qtc.pyqtSlot(int, qtc.QObject)
    def insert(self, row, item):
        """Insert an object into the model at the given row."""
        was_modified = self._modified
        self._modified = None

        # Signal any attached views that we are about to insert a row
        self.beginInsertRows(qtc.QModelIndex(), row, row)

        # Insert the object
        self._current.insert(row, item)
        item.setParent(self)
        if self._listen:
            self._connect_to(item)

        # Emit change signals
        if self.modified != was_modified:
            self.modifiedChanged.emit()

        # Signal any attached views that we are done inserting rows
        self.endInsertRows()

    modifiedChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(bool, notify=modifiedChanged)
    def modified(self):
        """Return True if objects have been added to or removed from the model since the last apply(), or if any
         of the objects in the model have been modified."""
        # If the cached value is still valid, use it
        if self._modified is not None:
            return self._modified

        # Compare the lists, then check the objects if necessary
        if self._original != self._current:
            self._modified = True
        else:
            for obj in self._current:
                if obj.modified:
                    self._modified = True
                    break

        self._modified = self._modified or False
        return self._modified

    @qtc.pyqtSlot()
    def apply(self):
        """Save the current state of the model, and call apply() on all contained objects."""
        was_modified = self._modified
        self._modified = None

        for obj in self._current:
            obj.apply()

        self._original = list(self._current)

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtc.pyqtSlot()
    def revert(self):
        """Discard modifications to the model. Each object contained in the model has its revert() method called."""
        was_modified = self._modified
        self._modified = None

        for obj in self._current:
            obj.revert()

        self._current = list(self._original)

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtc.pyqtSlot(int, int, result=qtc.QModelIndex)
    def index(self, row, col, parent=qtc.QModelIndex()):
        """Return a model index for the given row and column."""
        if row >= self.rowCount() or col >= self.columnCount():
            return qtc.QModelIndex()

        return self.createIndex(row, col, self[row])

    @qtc.pyqtSlot(int, result=qtc.QModelIndex)
    def parent(self, index):
        """Return the parent QModelIndex of the given index. ObjectModel only supports list and table access,
        so this function always returns an invalid index."""
        return qtc.QModelIndex()

    @qtc.pyqtSlot(result=int)
    def rowCount(self, parent=qtc.QModelIndex()):
        """Return the number of rows in the model."""
        return len(self)

    @qtc.pyqtSlot(result=int)
    def columnCount(self, parent=qtc.QModelIndex()):
        """Return the number of columns in the model."""
        return len(self._column_names) or 1

    @qtc.pyqtSlot(qtc.QModelIndex, int, result=qtc.QVariant)
    def data(self, index, role=qtc.Qt.DisplayRole):
        """If role matches one of the values provided by roleNames(), returns the value of that property for the
        object specified by index. Otherwise, the property is looked up by both the row and column of the index."""
        if not index.isValid():
            return qtc.QVariant()

        obj = self._current[index.row()]
        if role not in self._role_to_prop and role not in self._ref_role_to_prop:
            role = self._column_to_role[index.column()]

        if role in self._role_to_prop:
                return getattr(obj, self._role_to_prop[role])
        elif role in self._ref_role_to_prop:
            return getattr(obj.ref, self._ref_role_to_prop[role])

    def roleNames(self):
        """Return a dictionary containing the indices and encoded role names of the roles this model recognizes.
        The role names correspond to the pyqtProperty they modfiy."""
        return {k: v.encode() for k, v in itertools.chain(self._role_to_prop.items(), self._ref_role_to_prop.items())}

    @qtc.pyqtSlot(str, result=int)
    def role(self, name):
        """Return the role (int) with a given name."""
        for r, n in itertools.chain(self._role_to_prop.items(), self._ref_role_to_prop.items()):
            if n == name:
                return r
        else:
            return -1

    @qtc.pyqtSlot(qtc.QVariant)
    def setColumns(self, *args):
        """Set the model's columns to the properties named in the arguments. If there are no arguments, ObjectModel
        uses the names of the roles, in the order they appear; if the argument is a QVariant, it assumes this is a
        javascript array passed from QML; otherwise, it assumes the arguments are the names of the properties to use
        for the columns."""
        if not args:
            self._column_to_role = {col: role for col, role in enumerate(itertools.chain(self._role_to_prop.keys(),
                                                                                         self._ref_role_to_prop.keys()))}
            self._column_names = [prop for prop in itertools.chain(self._role_to_prop.values(),
                                                                   self._ref_role_to_prop.values())]
            return

        names = args[0].toVariant() if isinstance(args[0], qtc.QVariant) else list(map(lambda a: str(a), args))
        self._column_names = names

        self._column_to_role = {}
        for col, name in enumerate(names):
            try:
                role = next(filter(lambda rn: rn[1] == name, itertools.chain(self._role_to_prop.items(),
                                                                             self._ref_role_to_prop.items())))[0]
            except:
                continue

            self._column_to_role[col] = role

    @qtc.pyqtSlot(str, result=int)
    def fieldIndex(self, prop):
        """Return the column for a given property name."""
        try:
            return self._column_names.index(prop)
        except ValueError:
            return -1

    def _connect_to(self, obj):
        """Connects to an object's property change signals."""
        if obj is None:
            return
        elif isinstance(obj, self._type):
            roles = self._role_to_prop
            self._connect_to(getattr(obj, 'ref', None))
        elif isinstance(obj, self._ref_type):
            roles = self._ref_role_to_prop

        for num, name in roles.items():
            signal_name = name + 'Changed'

            try:
                signal = getattr(obj, signal_name)
            except AttributeError:
                continue

            if roles is self._role_to_prop:
                # if name not in self._slot_partials:
                #     self._slot_partials[name] = self.onChildModified #lambda p=name: self.onChildModified(p)

                signal.connect(self.onChildModified) #self._slot_partials[name])

            if roles is self._ref_role_to_prop:
                # if name not in self._ref_slot_partials:
                #     self._ref_slot_partials[name] = self.onChildRefModified #lambda p=name: self.onChildRefModified(p)

                signal.connect(self.onChildRefModified) #self._ref_slot_partials[name])

    def _disconnect_from(self, obj):
        """Disconnects from an object's property change signals."""
        if obj is None:
            return
        elif isinstance(obj, self._type):
            roles = self._role_to_prop
        elif isinstance(obj, self._ref_type):
            roles = self._ref_role_to_prop
            self._disconnect_from(getattr(obj, 'ref', None))

        for num, name in roles.items():
            signal_name = name + 'Changed'

            try:
                signal = getattr(obj, signal_name)
                signal.disconnect(self.onChildModified if roles is self._role_to_prop else self.onChildRefModified)
            except (AttributeError, KeyError):
                continue

    def onChildModified(self, role_name=None):
        """Translates a child object's property change signal into a dataChanged signal, allowing views to react
        automatically to property changes."""
        sender = self.sender()

        try:
            row = self._copy.index(sender)      # Have to access parent data member directly (index() is overridden
                                                # by QAbstractItemModel)
        except ValueError:
            return

        # try:
        #     col = self._column_names.index(role_name)
        # except ValueError:
        #     col = 0
        #
        # roles = [r for r, p in self._role_to_prop.items() if p == role_name]
        #
        # index = self.createIndex(row, col)
        # self.dataChanged.emit(index, index, roles)
        index1 = self.createIndex(row, 0)
        index2 = self.createIndex(row, self.columnCount() - 1)
        self.dataChanged.emit(index1, index2)

        before = self.modified
        self._modified = None
        if self.modified != before:
            self.modifiedChanged.emit()

    def onChildRefModified(self, role_name=None):
        """Translates a referenced object's property change signals into dataChanged signals, allowing connected views
        to update automatically."""
        sender = self.sender()

        for row, obj in enumerate(self):
            if obj.ref is sender:
                break
        else:
            return

        # try:
        #     col = self._column_names.index(role_name)
        # except ValueError:
        #     col = 0
        #
        # roles = [r for r, p in self._ref_role_to_prop.items() if p == role_name]
        #
        # index = self.createIndex(row, col)
        # self.dataChanged.emit(index, index, roles)
        index1 = self.createIndex(row, 0)
        index2 = self.createIndex(row, self.columnCount() - 1)
        self.dataChanged.emit(index1, index2)

        before = self.modified
        self._modified = None
        if self.modified != before:
            self.modifiedChanged.emit()

    @property
    def document(self):
        return [o.document for o in self._current]

    @property
    def deleted(self):
        """Returns objects that have been deleted from the Model. This can behave strangely if an object with
        the same id has been added to the list more than once."""
        # The mess of stuff below is functionally equivalent to
        # the following commented lines, but runs MUCH faster.
        #
        # [i for i in self._original if i not in self._copy]

        original_ids = {id(o) for o in self._original}
        copy_ids = {id(o) for o in self._current}
        deleted_ids = original_ids - copy_ids
        deleted_objs = [o for o in self._original if id(o) in deleted_ids]

        return deleted_objs

    @qtc.pyqtSlot(str, qtc.QVariant, result=int)
    def matchOne(self, role_name, value):
        """Return the index of the first item in the model where role_name equals value, or -1 if there are no
        matches."""
        for idx, item in enumerate(self):
            try:
                model_value = getattr(item, role_name)
            except AttributeError:
                continue

            if model_value == value:
                return idx
        else:
            return -1

    @qtc.pyqtSlot(str, result=qtc.QVariant)
    def min(self, role_name):
        """Returns the minimum of the values of role_name."""
        if not len(self):
            return None

        values = [getattr(o, role_name, None) for o in self]
        values = [v for v in values if v is not None]
        return min(values)

    @qtc.pyqtSlot(str, result=qtc.QVariant)
    def max(self, role_name):
        """Returns the maximum for the given role name. Values of None and missing attributes are ignored."""
        if not len(self):
            return None

        values = [getattr(o, role_name, None) for o in self]
        values = [v for v in values if v is not None]
        return max(values)


########################################################################################################################


def ObjectModelProperty(_type, key, **kwargs):
    """Shorthand for using MapProperty to create an ObjectModel property."""
    kwargs.pop('default', None)
    default_set = kwargs.get('default_set', None)
    default_set = default_set if default_set is not None else lambda self: ObjectModel(_type, parent=self)

    return Property(ObjectModel,
                    key,
                    enforce_type=ObjectModel,
                    convert_type=lambda self, value: ObjectModel(_type, objects=value, parent=self),
                    default_set=default_set,
                    **kwargs)
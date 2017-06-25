import abc, collections, datetime, itertools, sip, types
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq
from bson.json_util import dumps as json_dumps


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
    def from_document(document, default_type='MapObject', **kwargs):
        """Creates a MapObject subclass from a document. If the appropriate subclass can't be determined from the
        document contents, default_type is used. If no default_type is provided, the object will be a MapObject.
        Any remaining arguments (such as parent) are passed on to the new object's constructor."""
        _type = document.get('_type', None)
        object_type = MapObjectMetaclass.subclasses.get(_type, None) or MapObject._subclass(default_type)

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
        elif _type is not None and issubclass(_type, MapObject):
            return _type
        else:
            raise ValueError('%s is not a subclass of MapObject.' % _type)

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
        enforce_type = kwargs.get('enforce_type', lambda x: x)
        convert_type = kwargs.get('convert_type', lambda self, v: enforce_type(v))

        try:
            value = self[key]
        except KeyError:
            if 'default' in kwargs:
                # Get the default value
                default = kwargs.get('default')
                value = default(self) if callable(default) else default

                # Enforce type
                value = enforce_type(value)

                # Set value in the map if default_set is True
                if kwargs.get('default_set', False):
                    self[key] = value

                return value
            else:
                raise
        else:
            if type(value) is not enforce_type:
                value = convert_type(self, value)
                self[key] = value

            return value


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

    @property
    def original(self):
        """Return the original version of the document and sub-documents."""
        return types.MappingProxyType(self._map)

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


def Property(key, _type, fget=None, fset=None, read_only=False, **kwargs):
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

    fget = fget if fget is not None else (lambda self: MapObject.getValue(self, key, **fget_kwargs))

    if 'notify' in kwargs:
        fset = fset if fset is not None else (lambda self, value: MapObject.setValue(self, key, value, kwargs['notify'].__get__(self)))
    else:
        fset = fset if fset is not None else (lambda self, value: MapObject.setValue(self, key, value))

    if read_only:
        fset = None

    return qtc.pyqtProperty(_type, fget=fget, fset=fset, **kwargs)


########################################################################################################################


def MapObjectProperty(key, _type=MapObject, **kwargs):
    """Convenience function for creating MapObject properties."""
    default = kwargs.pop('default', None) if 'default' in kwargs else lambda self: _type()
    default_set = kwargs.pop('default_set', None) if 'default_set' in kwargs else True
    convert_type = lambda self, value: _type(value)

    return Property(key, _type,
                    enforce_type=_type,
                    convert_type=convert_type,
                    default=default,
                    default_set=default_set,
                    **kwargs)


########################################################################################################################


def ListProperty(key, **kwargs):
    """Convenience function for creating ListObject properties."""
    convert_type = lambda self, value: list(value)
    return Property(key, qtc.QVariant, enforce_type=list, convert_type=convert_type, **kwargs)


########################################################################################################################


def DateTimeProperty(key, **kwargs):
    """Convenience function for create datetime/QDateTime properties."""
    convert_type = lambda self, value: datetime.datetime.fromtimestamp(value.toSecsSinceEpoch(), datetime.timezone.utc)
    return Property(key, qtc.QDateTime, enforce_type=datetime.datetime, convert_type=convert_type, **kwargs)


########################################################################################################################


class MapObjectReferenceMetaclass(MapObjectMetaclass):

    def __init__(cls, *args, **kwargs):
        ref_type = args[2]['referent_type']
        if ref_type == MapObject.__name__:
            super().__init__(*args, **kwargs)
            return

        props = MapObjectMetaclass.properties[ref_type]

        for name in props:
            if name in dir(cls):
                continue

            fset = lambda self, value, n=name: setattr(self.ref, n, value)
            fget = lambda self, n=name: getattr(self.ref, n)
            setattr(cls, name + 'Changed', qtc.pyqtSignal())
            setattr(cls, name, qtc.pyqtProperty(qtc.QVariant, fget=fget, fset=fset))

        super().__init__(*args, **kwargs)


########################################################################################################################


class MapObjectReference(MapObject, metaclass=MapObjectReferenceMetaclass):
    """Holds a reference to another object in the database."""
    referent_type = 'MapObject'

    referentId = Property('referent_id', qtc.QVariant, default=None)
    referentType = Property('referent_type', str, default=referent_type)

    autoLoadChanged = qtc.pyqtSignal()
    autoLoad = Property('auto_load', bool, notify=autoLoadChanged, default=False)

    def _mirrored_signals(self, obj):
        signals = []
        for prop in MapObjectMetaclass.properties[self.referentType]:
            signal_name = prop + 'Changed'
            if isinstance(getattr(obj, signal_name, None), qtc.pyqtBoundSignal) \
                and hasattr(self, signal_name) and not hasattr(MapObject, signal_name):
                signals.append(signal_name)
        return signals

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
        if self._ref is not None:
            for signal_name in self._mirrored_signals(self._ref):
                getattr(self._ref, signal_name).disconnect(getattr(self, signal_name))

        if item is not None:
            if not isinstance(item, MapObject):
                raise TypeError('Expected MapObject or subclass, got %s' % type(item))

            self._ref = item
            self.referentId = item.id
            self.referentType = getattr(item, '_type', type(item).__name__)

            for signal_name in self._mirrored_signals(item):
                    getattr(item, signal_name).connect(getattr(self, signal_name))
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

    def __init__(self, _type, objects=None, listen=True, parent=None):
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

        # Discover property names for content and referenced objects and assign role numbers
        props = MapObjectMetaclass.properties[self._type.__name__]
        self._role_to_prop = {r: p for r, p in enumerate(props, qtc.Qt.UserRole)}

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

        self._original = list(self._current)

        for obj in self._current:
            obj.apply()

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtc.pyqtSlot()
    def revert(self):
        """Discard modifications to the model. Each object contained in the model has its revert() method called."""
        was_modified = self._modified
        self._modified = None

        # Re-connect and re-parent objects that were removed (which will be re-added)
        deleted = self.deleted
        for obj in deleted:
            self._connect_to(obj)
            obj.setParent(self)

        # Objects that are going to be removed should be disconnected and re-parented
        for obj in self._current:
            if obj not in self._original:
                self._disconnect_from(obj)
                obj.setParent(None)

        self._current = list(self._original)

        for obj in self._current:
            obj.revert()

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
        if role not in self._role_to_prop:
            role = self._column_to_role[index.column()]

        return getattr(obj, self._role_to_prop[role])

    def roleNames(self):
        """Return a dictionary containing the indices and encoded role names of the roles this model recognizes.
        The role names correspond to the pyqtProperty they modfiy."""
        return {k: v.encode() for k, v in self._role_to_prop.items()}

    @qtc.pyqtSlot(str, result=int)
    def role(self, name):
        """Return the role (int) with a given name."""
        for r, n in self._role_to_prop.items():
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
            self._column_to_role = {col: role for col, role in enumerate(self._role_to_prop.keys())}
            self._column_names = [prop for prop in self._role_to_prop.values()]
            return

        names = args[0].toVariant() if isinstance(args[0], qtc.QVariant) else list(map(lambda a: str(a), args))
        self._column_names = names

        self._column_to_role = {}
        for col, name in enumerate(names):
            try:
                role = next(filter(lambda rn: rn[1] == name, self._role_to_prop.items()))
            except:
                continue

            self._column_to_role[col] = role

    @qtc.pyqtSlot(qtc.QVariant)
    def columnNames(self):
        """Return the model's column names as a list of strings."""
        return list(self._column_names)

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

        for num, name in self._role_to_prop.items():
            signal_name = name + 'Changed'

            try:
                signal = getattr(obj, signal_name)
            except AttributeError:
                continue

            signal.connect(self.onChildModified)

    def _disconnect_from(self, obj):
        """Disconnects from an object's property change signals."""
        if obj is None:
            return

        for num, name in self._role_to_prop.items():
            signal_name = name + 'Changed'

            try:
                signal = getattr(obj, signal_name)
                signal.disconnect(self.onChildModified)
            except (AttributeError, KeyError):
                continue

    def onChildModified(self):
        """Translates a child object's property change signal into a dataChanged signal, allowing views to react
        automatically to property changes."""
        sender = self.sender()

        try:
            row = self._current.index(sender)
        except ValueError:
            return

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
    def original(self):
        return list(self._original)

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


def ObjectModelProperty(key, _type=MapObject, **kwargs):
    """Shorthand for using MapProperty to create an ObjectModel property."""
    default = kwargs.pop('default', None) if 'default' in kwargs else lambda self: ObjectModel(_type)
    default_set = kwargs.pop('default_set', None) if 'default_set' in kwargs else True

    return Property(key, ObjectModel,
                    enforce_type=ObjectModel,
                    convert_type=lambda self, value: ObjectModel(_type, objects=value),
                    default=default,
                    default_set=default_set,
                    **kwargs)
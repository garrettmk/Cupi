import abc, collections, datetime, itertools, sip, types
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq
from bson.json_util import dumps as json_dumps


########################################################################################################################


class DocumentObjectMetaclass(sip.wrappertype, abc.ABCMeta):
    """DocumentObjectMetaclass provides a QObject-compatible metaclass for DocumentObject."""
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)


########################################################################################################################


class DocumentObject(qtc.QObject):
    """
    DocumentObject is the base class for qp documents (MapObject and ListObject). It defines the basic interface
    shared by all document types: a "modified" property and signal, apply(), revert(), and a document property.
    """
    def _process_input(self, item):
        """Converts non-string sequences and mappings to DocumentObjects. Leaves other inputs unchanged."""
        if isinstance(item, collections.Sequence) and not isinstance(item, (str, ListObject)):
            lo = ListObject(item, parent=self)
            lo.modifiedChanged.connect(self.modifiedChanged)
            return lo
        elif isinstance(item, collections.Mapping) and not isinstance(item, MapObject):
            mo = MapObject.from_document(item, parent=self)
            mo.modifiedChanged.connect(self.modifiedChanged)
            return mo

        return item

    modified = NotImplemented
    modifiedChanged = NotImplemented

    @property
    def document(self):
        """Recursively generates JSON document from this object and its children. The result is expressed using
        plain Python lists and dicts."""
        raise NotImplementedError

    @qtc.pyqtSlot()
    def apply(self):
        """Applies any changes to the document. This causes the modified property to be reset."""
        raise NotImplementedError

    @qtc.pyqtSlot()
    def revert(self):
        """Deletes any modifications to the document and restores it to its original state. This causes the
        modified property to be reset."""
        raise NotImplementedError


########################################################################################################################


class ListObject(DocumentObject, collections.MutableSequence, metaclass=DocumentObjectMetaclass):
    """
    ListObject provides document tracking to list-based documents. Changes are tracked, modifications are signalled.

    ListObject inherits from collections.Sequence, and can be used anywhere a Python list can be used.
    """

    def __init__(self, iterable=None, parent=None):
        """Initialize the ListObject. If the parent argument is provided, it is passed to the QObject constructor.
        All other arguments are used to set the initial state of the list."""

        super().__init__(parent=parent)

        iterable = [] if iterable is None else iterable
        self._original = [self._process_input(i) for i in iterable]
        self._copy = list(self._original)

        # Storing the modification state isn't strictly necessary, but self.modified gets called so
        # often that caching it's result helps performance
        self._modified = None
        self.modified

    def __getitem__(self, index):
        """Retrieve the item at the given index. Note that slicing returns a list object, NOT a ListObject."""
        return self._copy[index]

    def __setitem__(self, index, item):
        """Modifies the item at the given index."""
        was_modified = self._modified
        self._modified = None

        self._copy[index] = item.toVariant() if isinstance(item, qtq.QJSValue) else item

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    def __delitem__(self, index):
        """Delete the item at the specified index."""
        was_modified = self._modified
        self._modified = None

        del self._copy[index]

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtc.pyqtSlot(int, qtc.QVariant)
    def insert(self, index, item):
        """Insert an item at the given index."""
        was_modified = self._modified
        self._modified = None

        self._copy.insert(index, item)

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtc.pyqtSlot(qtc.QVariant)
    def append(self, item):
        """Append an item to the list."""
        super().append(item)

    def __len__(self):
        """Return the number of items in the list."""
        return len(self._copy)

    @qtc.pyqtSlot(result=int)
    def length(self):
        """Convenience function for accessing len() from QML."""
        return len(self)

    def __iter__(self):
        """Return an iterator for the list."""
        return iter(self._copy)

    modifiedChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(bool, notify=modifiedChanged)
    def modified(self):
        """True if the list has been modified since the last save."""
        # If we still have a valid cached value, use that
        if self._modified is None:
            self._modified = False

            # Compare the lists, then check the items if necessary
            if self._original != self._copy:
                self._modified = True
            else:
                for item in self._copy:
                    if isinstance(item, DocumentObject) and item.modified:
                        self._modified = True
                        break

        return self._modified

    @qtc.pyqtSlot(int, result=qtc.QVariant)
    def getItem(self, index):
        """Convenience function for accessing items from QML."""
        return self[index]

    @qtc.pyqtSlot(int, qtc.QVariant)
    def setItem(self, index, item):
        """Convenience function for setting items from QML."""
        self[index] = item

    @qtc.pyqtSlot()
    def apply(self, apply_children=True):
        """Save the current state of the list. Resets the modified property."""
        was_modified = self._modified
        self._modified = None

        if apply_children:
            for obj in self._copy:
                if isinstance(obj, DocumentObject):
                    obj.apply()

        self._original = list(self._copy)

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtc.pyqtSlot()
    def revert(self, revert_children=True):
        """Discard any modifications made since the last save."""
        was_modified = self._modified
        self._modified = None

        if revert_children:
            for obj in self._original:
                if isinstance(obj, DocumentObject):
                    obj.revert()

        self._copy = list(self._original)

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @property
    def document(self):
        response = []

        for item in self:
            if isinstance(item, DocumentObject):
                response.append(item.document)
            else:
                response.append(item)

        return response

    @property
    def original(self):
        return tuple(self._original)



########################################################################################################################


class MapObjectMetaclass(DocumentObjectMetaclass):
    """
    When loading MapObject-derived classes from JSON documents, it is necessary to look up a subclass by name. Also,
    when an ObjectModel is created for a certain type, it must look at that types attributes and determine which ones
    are pyqtProperty's. Because these are lengthy operations that must be done frequently, MapObjectMetaclass keeps
    track of the information and makes it available.

    subclasses:         A dictionary relating class names to their types.
    map_properties:     A dictionary relating class names to a list of property names (the pyqtProperty attributes of
                        the class)
    """
    subclasses = {}
    map_properties = {}

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = args[0]
        MapObjectMetaclass.subclasses[name] = cls
        MapObjectMetaclass.map_properties[name] = [p for p in dir(cls) if isinstance(getattr(cls, p), qtc.pyqtProperty)]


########################################################################################################################


class MapObject(DocumentObject, collections.MutableMapping, metaclass=MapObjectMetaclass):
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
    def subtype(_type):
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
    def all_subclass_names(cls):
        """Returns a list with the names of all of this classes' subclasses."""
        return [c.__name__ for c in cls.__subclasses__()] + [g for s in cls.__subclasses__() \
                                                             for g in s.all_subclass_names()]

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
        prop_kwargs = {kw: value for kw, value in kwargs.items() if kw in MapObjectMetaclass.map_properties[type(self).__name__]}
        kwargs = {kw: value for kw, value in kwargs.items() if kw not in prop_kwargs}

        # Call the parent constructors
        super().__init__(parent=kwargs.pop('parent', None))

        # Initialize members
        self._map = {k: self._process_input(v) for k, v in dict(*args, **kwargs).items()}
        self._mods = dict()
        self._dels = set()
        self._modified = False

        _type = type(self)
        if '_type' not in self and _type is not MapObject:
            self._map['_type'] = _type.__name__

        # Initialize properties
        for prop, value in prop_kwargs.items():
            setattr(self, prop, value)

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
                or self._map[key] != value:
            # It's a new key, or a modification of the original key's value
            self._mods[key] = value
        else:
            # We are setting a key back to its original value
            self._mods.pop(key, None)

        # If this key was marked as deleted, clear it
        self._dels.discard(key)

        # If modification status changed, emit the signal
        if self.modified != was_modified:
            self.modifiedChanged.emit()

    def __delitem__(self, key):
        """Delete a key-value pair."""
        if not (key in self._map or key in self._mods) \
                or key in self._dels:
            # key is not in the map and it's not in the mods
            raise KeyError(key)
        else:
            was_modified = self._modified

            self._mods.pop(key, None)
            if key in self._map:
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
            if isinstance(item, DocumentObject) and item.modified:
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
            if isinstance(item, DocumentObject):
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
            if isinstance(value, DocumentObject):
                value.revert()

        self._mods.clear()
        self._dels.clear()

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @property
    def document(self):
        response = {}

        for key, value in self.items():
            if isinstance(value, DocumentObject):
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

    typeChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(str, notify=typeChanged)
    def type(self):
        """Return the object's type as a string."""
        return self['_type']


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
    default_set = default_set if default_set is not None else lambda self: datetime.datetime.now(datetime.timezone.utc)
    convert_type = lambda self, value: datetime.datetime.fromtimestamp(value.toSecsSinceEpoch(), datetime.timezone.utc)

    return Property(qtc.QDateTime,
                    key,
                    enforce_type=datetime.datetime,
                    convert_type=convert_type,
                    default_set=default_set,
                    **kwargs)


########################################################################################################################


class MapObjectReference(MapObject):
    """Holds a reference to another object in the database."""

    referencedId = Property(str, 'referenced_id', default=None)
    referencedType = Property(str, 'referenced_type', default='')

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
            self.referencedId = item.get('_id', None)
            self.referencedType = getattr(item, '_type', type(item).__name__)
        else:
            self._ref = None
            self.referencedId = ''
            self.referencedType = ''

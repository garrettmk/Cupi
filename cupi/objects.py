import abc, collections, itertools, sip, types
import PyQt5.QtCore as qtcore
import PyQt5.QtQml as qtqml


########################################################################################################################


class DocumentObjectMetaclass(sip.wrappertype, abc.ABCMeta):
    """DocumentObjectMetaclass provides a QObject-compatible metaclass for DocumentObject."""
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)


########################################################################################################################


class DocumentObject(qtcore.QObject):
    """
    DocumentObject is the base class for qp documents (MapObject and ListObject). It defines the basic interface
    shared by all document types: a "modified" property and signal, apply(), revert(), and a document property.
    """
    def _process_input(self, item):
        """Converts non-string sequences and mappings to DocumentObjects. Leaves other inputs unchanged."""
        if isinstance(item, collections.Sequence) and not isinstance(item, (str, ListObject)):
            return ListObject(item, parent=self)
        elif isinstance(item, collections.Mapping) and not isinstance(item, MapObject):
            return MapObject.from_document(item, parent=self)

        return item

    modified = NotImplemented

    @property
    def document(self):
        """Recursively generates JSON document from this object and its children. The result is expressed using
        plain Python lists and dicts."""
        raise NotImplementedError

    @qtcore.pyqtSlot()
    def apply(self):
        """Applies any changes to the document. This causes the modified property to be reset."""
        raise NotImplementedError

    @qtcore.pyqtSlot()
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

        self._copy[index] = item.toVariant() if isinstance(item, qtqml.QJSValue) else item

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    def __delitem__(self, index):
        """Delete the item at the specified index."""
        was_modified = self._modified
        self._modified = None

        del self._copy[index]

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtcore.pyqtSlot(int, qtcore.QVariant)
    def insert(self, index, item):
        """Insert an item at the given index."""
        was_modified = self._modified
        self._modified = None

        self._copy.insert(index, item)

        if self.modified != was_modified:
            self.modifiedChanged.emit()

    @qtcore.pyqtSlot(qtcore.QVariant)
    def append(self, item):
        """Append an item to the list."""
        super().append(item)

    def __len__(self):
        """Return the number of items in the list."""
        return len(self._copy)

    @qtcore.pyqtSlot(int)
    def length(self):
        """Convenience function for accessing len() from QML."""
        return len(self)

    def __iter__(self):
        """Return an iterator for the list."""
        return iter(self._copy)

    modifiedChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(bool, notify=modifiedChanged)
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

    @qtcore.pyqtSlot(int, result=qtcore.QVariant)
    def getItem(self, index):
        """Convenience function for accessing items from QML."""
        return self[index]

    @qtcore.pyqtSlot(int, qtcore.QVariant)
    def setItem(self, index, item):
        """Convenience function for setting items from QML."""
        self[index] = item

    @qtcore.pyqtSlot()
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

    @qtcore.pyqtSlot()
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
    subclasses = {}

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = args[0]
        MapObjectMetaclass.subclasses[name] = cls


########################################################################################################################


class MapObject(DocumentObject, collections.MutableMapping, metaclass=MapObjectMetaclass):
    """
    The primary purpose of MapObject is to provide property access to a dictionary of key/value pairs.
    It supports the DocumentObject interface, tracks changes and signals on modification.

    MapObject inherits from collections.MutableMapping, and can be used as a dictionary. Key/value pairs can be
    accessed from QML by either using getValue()/setValue(), or by declaring properties using MapProperty().
    """

    @staticmethod
    def from_document(document, default_type=None, **kwargs):
        """Creates a MapObject subclass from a document. If the appropriate subclass can't be determined from the
        document contents, default_type is used. If no default_type is provided, the object will be a MapObject.
        Any remaining arguments (such as parent) are passed on to the new object's constructor."""
        if '_type' in document and document['_type'] in MapObjectMetaclass.subclasses:
            object_type = MapObjectMetaclass.subclasses[document['_type']]
        else:
            object_type = default_type or MapObject

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
        elif not issubclass(_type, MapObject):
            raise TypeError('%s is not a subclass of MapObject.' % _type)
        else:
            return _type

    @staticmethod
    def register_subclasses():
        """Automatically registers all subclasses with the QML engine."""
        for name, _type in MapObjectMetaclass.subclasses.items():
            qtqml.qmlRegisterType(_type, name, 1, 0, name)

    def __init__(self, *args, **kwargs):
        """Initialize the MapObject. If the parent argument is provided, it is passed to the QObject constructor.
        All other arguments are used to set the initial state of the map."""

        # Creating an object from QML passes (None,) as constructor arguments. Get rid of this so it doesn't
        # mess up the dict constructor down the line.
        if args == (None,):
            args = ()

        super().__init__(parent=kwargs.pop('parent', None))

        self._map = {k: self._process_input(v) for k, v in dict(*args, **kwargs).items()}
        self._mods = dict()
        self._dels = set()

        # Cache the modification state to help performance
        self._modified = False

        _type = type(self)
        if '_type' not in self and _type is not MapObject:
            self._map['_type'] = _type.__name__

    @qtcore.pyqtSlot(str, result=qtcore.QVariant)
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
            return self[key]
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

    @qtcore.pyqtSlot(str, qtcore.QVariant)
    def setValue(self, key, value, *args):
        """Assigns value to key in the map. Any additional arguments are assumed to be notification signals, and
        their emit() attribute is called."""
        self[key] = value.toVariant() if isinstance(value, qtqml.QJSValue) else value
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

    modifiedChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(bool, notify=modifiedChanged)
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

    @qtcore.pyqtSlot()
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

    @qtcore.pyqtSlot()
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


########################################################################################################################


def MapProperty(type, key, fget=None, fset=None, **kwargs):
    """Creates a property that uses MapObject's getValue() and setValue() functions as getter and setter. Supports
    defaults and notification signals. MapProperty() is a convenience wrapper for pyqtProperty().

    Arguments:
        type                    The type of the property.
        key                     The key assigned to this property.
        notify                  (optional) The notification signal assigned to this property.
        default, default_set    (optional) Passed on to MapObject.getValue()

    Usage:  class PropertyMap(MapObject):
                onXChanged = pyqtSignal()
                x = MapProperty(str, 'x', notify=onXChanged, default='n/a')

    """
    fget_kwargs = {k:v for k, v in kwargs.items() if k in ['default', 'default_set']}
    kwargs = {k: v for k, v in kwargs.items() if k not in fget_kwargs}

    fget = fget or (lambda self: MapObject.getValue(self, key, **fget_kwargs))

    if 'notify' in kwargs:
        fset = fset or (lambda self, value: MapObject.setValue(self, key, value, kwargs['notify'].__get__(self)))
    else:
        fset = fset or (lambda self, value: MapObject.setValue(self, key, value))

    return qtcore.pyqtProperty(type, fget=fget, fset=fset, **kwargs)

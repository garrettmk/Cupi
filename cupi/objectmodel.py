from .objects import *


########################################################################################################################


class ObjectModel(qtc.QAbstractItemModel, ListObject):
    """ObjectModel provides a QAbstractItemModel interface to a list of qp.MapObject objects. It will automatically
    provide 'role' names based on the object types properties, and can be used as either a list or a table model.
    It also implements the collections.MutableSequence interface, so it can be used as a Python list as well.
    """

    # QML doesn't read the inherited properly correctly, because we are inheriting from QAbstractItemModel first...?
    modifiedChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(bool, notify=modifiedChanged)
    def modified(self):
        #return len(self.deleted) > 0
        return super().modified

    def __init__(self, _type, ref_type=None, objects=None, listen=True, parent=None):
        """Initializes the model. _type is a qp.Object subclass, which will be used to determine the role names
        the model provides. objects is the list of objects to use. If listen is True (the default) the model will
        connect to any property change signals the object type provides, and will translate those to dataChanged
        signals.
        """
        super().__init__([] if objects is None else objects, parent=parent)
        self._type = None
        self._ref_type = None
        self._listen = listen
        self._role_to_prop = {}
        self._ref_role_to_prop = {}
        self._column_to_role = {}
        self._column_names = []

        # Take ownership of content objects
        for obj in self:
            obj.setParent(self)

        # Validate the type for both content objects and referenced objects (if applicable)
        self._type = MapObject.subtype(_type)

        # If this is a list of object references, try to determine the type of the referenced objects. Use the explicit
        # argument if provided, otherwise ask the referencing type.
        if issubclass(_type, MapObjectReference):
            if ref_type is not None:
                self._ref_type = MapObject.subtype(ref_type)
            else:
                try:
                    self._ref_type = MapObject.subtype(self._type.referencedType)
                except (AttributeError, ValueError, TypeError):
                    raise TypeError('A valid reference type could not be determined.')

        # Discover role names for content and referenced objects
        props = [p for p in dir(_type) if isinstance(getattr(_type, p), qtc.pyqtProperty)]
        self._role_to_prop = {r: p for r, p in enumerate(props, qtc.Qt.UserRole)}

        if self._ref_type is not None:
            props = [p for p in dir(self._ref_type) if isinstance(getattr(self._ref_type, p), qtc.pyqtProperty)]
            self._ref_role_to_prop = {r: p for r, p in enumerate(props, max(self._role_to_prop) + 1)}

        # Set the default columns
        self.setColumns()

        # Connect to property change signals
        if listen:
            for obj in self:
                self._connect_to(obj)

    def __setitem__(self, index, item):
        current = self[index]
        if current is not item:
            self._disconnect_from(current)
            if current.parent() is self:
                current.setParent(None)

        super().__setitem__(index, item)
        item.setParent(self)
        if self._listen:
            self._connect_to(item)

        if current is not item:
            topleft = self.createIndex(index, 0)
            bottomright = self.createIndex(index, len(self._column_to_role))
            self.dataChanged.emit(topleft, bottomright)

    def __delitem__(self, row):
        self.removeRows(row, 1)

    @qtc.pyqtSlot(int, qtc.QObject)
    def insert(self, row, item):
        self.beginInsertRows(qtc.QModelIndex(), row, row)
        super().insert(row, item)
        self._connect_to(item)
        item.setParent(self)
        self.endInsertRows()

    @qtc.pyqtSlot(qtc.QObject)
    def append(self, item):
        self.insert(len(self), item)

    @qtc.pyqtSlot(int, result=bool)
    def removeRow(self, row, parent=qtc.QModelIndex()):
        return self.removeRows(row, 1, parent)

    @qtc.pyqtSlot(int, int, result=bool)
    def removeRows(self, row, count, parent=qtc.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)

        for i in range(count):
            obj = self[row]
            self._disconnect_from(obj)
            super().__delitem__(row)

        self.endRemoveRows()
        return True

    @qtc.pyqtSlot()
    def apply(self):
        for obj in self.deleted:
            if obj.parent() is self:
                obj.setParent(None)

        ListObject.apply(self, apply_children=False)

    @qtc.pyqtSlot()
    def revert(self):
        for obj in self.deleted:
            if obj.parent() is None:
                obj.setParent(self)

        ListObject.revert(self, revert_children=False)         # QAbstractItemModel also has a revert() method

    @qtc.pyqtSlot(int, result=qtc.QObject)
    def getItem(self, index):
        return super().getItem(index)

    @qtc.pyqtSlot(int, qtc.QObject)
    def setItem(self, index, item):
        return super().setItem(index, item)

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
        return len(self._column_to_role) or 1

    @qtc.pyqtSlot(qtc.QModelIndex, int, result=qtc.QVariant)
    def data(self, index, role=qtc.Qt.DisplayRole):
        """If role matches one of the values provided by roleNames(), returns the value of that property for the
        object specified by index. Otherwise, the property is looked up by both the row and column of the index."""
        if not index.isValid():
            return qtc.QVariant()

        obj = self[index.row()]
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
    def deleted(self):
        """Returns objects that have been deleted from the Model. This can behave strangely if an object with
        the same id has been added to the list more than once."""
        # The mess of stuff below is functionally equivalent to
        # the following commented lines, but runs MUCH faster.
        #
        # [i for i in self._original if i not in self._copy]

        original_ids = {id(o) for o in self._original}
        copy_ids = {id(o) for o in self._copy}
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
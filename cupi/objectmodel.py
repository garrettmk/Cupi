from .objects import *


########################################################################################################################


class ObjectModel(qtcore.QAbstractItemModel, ListObject):
    """ObjectModel provides a QAbstractItemModel interface to a list of qp.Object objects. It will automatically
    provide 'role' names based on the object types properties, and can be used as either a list or a table model.
    It also implements the collections.MutableSequence interface, so it can be used as a Python list as well.
    """

    # QML doesn't read the inherited properly correctly, because we are inheriting from QAbstractItemModel first...?
    modifiedChanged = qtcore.pyqtSignal()
    @qtcore.pyqtProperty(bool, notify=modifiedChanged)
    def modified(self):
        return super().modified

    def __init__(self, _type, objects=None, listen=True, parent=None):
        """Initializes the model. _type is a qp.Object subclass, which will be used to determine the role names
        the model provides. objects is the list of objects to use. If listen is True (the default) the model will
        connect to any property change signals the object type provides, and will translate those to dataChanged
        signals.
        """
        super().__init__([] if objects is None else objects, parent=parent)
        for obj in self:
            obj.setParent(self)

        self._type = _type
        self._role_to_prop = {}
        self._column_to_role = {}
        self._column_names = []
        self._listen = listen
        self._slot_partials = {}

        # Roles are stored as key/value pairs, where the key is an integer (starting with Qt.UserRole+1),
        # and the value is a byte string that represents the name of the role/property.
        props = filter(lambda x: type(getattr(_type, x)) == qtcore.pyqtProperty, dir(_type))
        self._role_to_prop = dict(enumerate(props, start=qtcore.Qt.UserRole + 1))
        self.setColumns()

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

    @qtcore.pyqtSlot(int, qtcore.QObject)
    def insert(self, row, item):
        self.beginInsertRows(qtcore.QModelIndex(), row, row)
        super().insert(row, item)
        self._connect_to(item)
        item.setParent(self)
        self.endInsertRows()

    @qtcore.pyqtSlot(qtcore.QObject)
    def append(self, item):
        self.insert(len(self), item)

    @qtcore.pyqtSlot(int, result=bool)
    def removeRow(self, row, parent=qtcore.QModelIndex()):
        return self.removeRows(row, 1, parent)

    @qtcore.pyqtSlot(int, int, result=bool)
    def removeRows(self, row, count, parent=qtcore.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)

        for i in range(count):
            obj = self[row]
            self._disconnect_from(obj)
            super().__delitem__(row)

        self.endRemoveRows()
        return True

    @qtcore.pyqtSlot()
    def apply(self):
        for obj in self.deleted:
            if obj.parent() is self:
                obj.setParent(None)

        ListObject.apply(self, apply_children=False)

    @qtcore.pyqtSlot()
    def revert(self):
        for obj in self.deleted:
            if obj.parent() is None:
                obj.setParent(self)

        ListObject.revert(self, revert_children=False)         # QAbstractItemModel also has a revert() method

    @qtcore.pyqtSlot(int, result=qtcore.QObject)
    def getItem(self, index):
        return super().getItem(index)

    @qtcore.pyqtSlot(int, qtcore.QObject)
    def setItem(self, index, item):
        return super().setItem(index, item)

    @qtcore.pyqtSlot(int, int, result=qtcore.QModelIndex)
    def index(self, row, col, parent=qtcore.QModelIndex()):
        """Return a model index for the given row and column."""
        if row >= self.rowCount() or col >= self.columnCount():
            return qtcore.QModelIndex()

        return self.createIndex(row, col, self[row])

    @qtcore.pyqtSlot(int, result=qtcore.QModelIndex)
    def parent(self, index):
        """Return the parent QModelIndex of the given index. ObjectModel only supports list and table access,
        so this function always returns an invalid index."""
        return qtcore.QModelIndex()

    @qtcore.pyqtSlot(result=int)
    def rowCount(self, parent=qtcore.QModelIndex()):
        """Return the number of rows in the model."""
        return len(self)

    @qtcore.pyqtSlot(result=int)
    def columnCount(self, parent=qtcore.QModelIndex()):
        """Return the number of columns in the model."""
        return len(self._column_to_role) or 1

    @qtcore.pyqtSlot(qtcore.QModelIndex, int, result=qtcore.QVariant)
    def data(self, index, role=qtcore.Qt.DisplayRole):
        """If role matches one of the values provided by roleNames(), returns the value of that property for the
        object specified by index. Otherwise, the property is looked up by both the row and column of the index."""
        if not index.isValid():
            return qtcore.QVariant()

        obj = self[index.row()]

        if role not in self._role_to_prop:
            try:
                role = self._column_to_role[index.column()]
            except KeyError:
                return qtcore.QVariant()
        try:
            return getattr(obj, self._role_to_prop[role])
        except:
            print('wait')

    def roleNames(self):
        """Return a dictionary containing the indices and encoded role names of the roles this model recognizes.
        The role names correspond to the pyqtProperty they modfiy."""
        return {k: v.encode() for k, v in self._role_to_prop.items()}

    @qtcore.pyqtSlot(qtcore.QVariant)
    def setColumns(self, *args):
        """Set the model's columns to the properties named in the arguments. If there are no arguments, ObjectModel
        uses the names of the roles, in the order they appear; if the argument is a QVariant, it assumes this is a
        javascript array passed from QML; otherwise, it assumes the arguments are the names of the properties to use
        for the columns."""
        if not args:
            self._column_to_role = {col: role for col, role in enumerate(self._role_to_prop.keys())}
            self._column_names = [prop for prop in self._role_to_prop.values()]
            return

        names = args[0].toVariant() if isinstance(args[0], qtcore.QVariant) else list(map(lambda a: str(a), args))
        self._column_names = names

        self._column_to_role = {}
        for col, name in enumerate(names):
            try:
                role = next(filter(lambda rn: rn[1] == name, self._role_to_prop.items()))[0]
            except:
                continue

            self._column_to_role[col] = role

    @qtcore.pyqtSlot(str, result=int)
    def fieldIndex(self, prop):
        """Return the column for a given property name."""
        try:
            return self._column_names.index(prop)
        except ValueError:
            return -1

    def _connect_to(self, obj):
        """Connects to an object's on(X)Changed() signals."""
        for num, name in self._role_to_prop.items():
            signal_name = name + 'Changed'

            try:
                signal = getattr(obj, signal_name)
            except AttributeError:
                continue

            if name not in self._slot_partials:
                self._slot_partials[name] = lambda p=name: self.onChildModified(p)

            signal.connect(self._slot_partials[name])

    def _disconnect_from(self, obj):
        """Disconnects from an object's on(X)Changed signals."""
        for num, name in self._role_to_prop.items():
            signal_name = name + 'Changed'

            try:
                signal = getattr(obj, signal_name)
                signal.disconnect(self._slot_partials[name])
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

        try:
            col = self._column_names.index(role_name)
        except ValueError:
            col = 0

        roles = [r for r, p in self._role_to_prop.items() if p == role_name]

        index = self.createIndex(row, col)
        self.dataChanged.emit(index, index, roles)

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
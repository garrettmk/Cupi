import abc, collections, itertools, sip
import PyQt5.QtCore as qtc
from .objects import MapObject, MapObjectReference, Property


# ########################################################################################################################
#
#
# class ObjectModelMetaclass(sip.wrappertype, abc.ABCMeta):
#     """A QObject-compatible metaclass for ObjectModel."""
#
#
# ########################################################################################################################
#
#
# class ObjectModel(qtc.QAbstractItemModel, collections.MutableSequence, metaclass=ObjectModelMetaclass):
#     """ObjectModel provides a QAbstractItemModel interface to a list of qp.MapObject objects. It will automatically
#     provide 'role' names based on the object types properties, and can be used as either a list or a table model.
#     It also implements the collections.MutableSequence interface, so it can be used as a Python list as well.
#     """
#
#     def __init__(self, _type, ref_type=None, objects=None, listen=True, parent=None):
#         """Initializes the model. _type is a qp.Object subclass, which will be used to determine the role names
#         the model provides. objects is the list of objects to use. If listen is True (the default) the model will
#         connect to any property change signals the object type provides, and will translate those to dataChanged
#         signals.
#         """
#         super().__init__(parent=parent)
#
#         self._original = objects if objects is not None else []
#         self._current = list(self._original)
#         self._removed = list()
#
#         # Take ownership of content objects
#         for obj in self:
#             obj.setParent(self)
#
#         # The type of object stored by the model
#         self._type = MapObject._subclass(_type)
#
#         # If self._type is a kind of ObjectReference, self._ref_type is the type of object stored by the reference
#         # If ref_type is not provided, try to determine the type by asking reference type
#         if issubclass(_type, MapObjectReference):
#             if ref_type is not None:
#                 self._ref_type = MapObject._subclass(ref_type)
#             else:
#                 try:
#                     self._ref_type = MapObject._subclass(self._type.referencedType)
#                 except (AttributeError, ValueError, TypeError):
#                     raise TypeError('A valid reference type could not be determined.')
#         else:
#             self._ref_type = None
#
#         # Discover property names for content and referenced objects and assign role numbers
#         props = [p for p in dir(_type) if isinstance(getattr(_type, p), qtc.pyqtProperty)]
#         self._role_to_prop = {r: p for r, p in enumerate(props, qtc.Qt.UserRole)}
#
#         if self._ref_type is not None:
#             props = [p for p in dir(self._ref_type) if isinstance(getattr(self._ref_type, p), qtc.pyqtProperty)]
#             self._ref_role_to_prop = {r: p for r, p in enumerate(props, max(self._role_to_prop) + 1)}
#
#         # Set the default column names
#         self._column_to_role = {}
#         self._column_names = []
#         self.setColumns()
#
#         # Connect to property change signals
#         self._listen = listen
#         if listen:
#             for obj in self:
#                 self._connect_to(obj)
#
#         # self.modified gets called so often that storing the modification state helps improve performance
#         self._modified = None
#         self.modified
#
#     def __getitem__(self, index):
#         """Retrieve the object at the given index."""
#         return self._current[index]
#
#     def __setitem__(self, index, item):
#         """Replace the object at the given index."""
#         was_modified = self._modified
#         self._modified = None
#
#         # Disconnect from the object currently in the list
#         current = self[index]
#         self._disconnect_from(current)
#         if current.parent() is self:
#             current.setParent(None)
#
#         # Replace the item in the list
#         self._current[index] = item
#         item.setParent(self)
#         if self._listen:
#             self._connect_to(item)
#
#         # Emit change signals
#         if self.modified != was_modified:
#             self.modifiedChanged.emit()
#             topleft = self.createIndex(index, 0)
#             bottomright = self.createIndex(index, len(self._column_to_role))
#             self.dataChanged.emit(topleft, bottomright)
#
#     def __delitem__(self, row):
#         """Remove an object from the model."""
#         self.removeRows(row, 1)
#
#     def __len__(self):
#         """Return the number of objects in the model."""
#         return len(self._current)
#
#     def __iter__(self):
#         """Return an iterator for the model."""
#         return iter(self._current)
#
#     @qtc.pyqtSlot(int, result=MapObject)
#     def getObject(self, index):
#         """Convenience function for accessing objects by index from QML."""
#         return self[index]
#
#     @qtc.pyqtSlot(int, MapObject)
#     def setObject(self, index, obj):
#         """Convenience function for assigning objects by index from QML."""
#         self[index] = obj
#
#     @qtc.pyqtSlot(int, int, result=bool)
#     def removeRows(self, row, count, parent=qtc.QModelIndex()):
#         """Starting at :row:, remove :count: rows from the model."""
#         was_modified = self._modified
#         self._modified = None
#
#         # Signal any attached views that we are about to change the model
#         self.beginRemoveRows(parent, row, row + count - 1)
#
#         # Remove the objects from the model
#         for i in range(count):
#             obj = self[row]
#             self._disconnect_from(obj)
#             if obj.parent() is self:
#                 obj.setParent(None)
#
#             del self._current[row]
#             self._removed.append(obj)
#
#         # Emit change signals
#         if self.modified != was_modified:
#             self.modifiedChanged.emit()
#
#         # Signal attached views that we are done changing the model
#         self.endRemoveRows()
#
#         return True
#
#     @qtc.pyqtSlot(int, result=bool)
#     def removeRow(self, row, parent=qtc.QModelIndex()):
#         """Remove the object at the given row from the model."""
#         return self.removeRows(row, 1, parent)
#
#     @qtc.pyqtSlot(result=int)
#     def length(self):
#         """Convenience function, returns the number of objects in the model."""
#         return len(self)
#
#     @qtc.pyqtSlot(qtc.QObject)
#     def append(self, item):
#         """Append an object to the end of the model."""
#         collections.MutableSequence.append(self, item)
#
#     @qtc.pyqtSlot(int, qtc.QObject)
#     def insert(self, row, item):
#         """Insert an object into the model at the given row."""
#         was_modified = self._modified
#         self._modified = None
#
#         # Signal any attached views that we are about to insert a row
#         self.beginInsertRows(qtc.QModelIndex(), row, row)
#
#         # Insert the object
#         self._current.insert(row, item)
#         item.setParent(self)
#         if self._listen:
#             self._connect_to(item)
#
#         # Emit change signals
#         if self.modified != was_modified:
#             self.modifiedChanged.emit()
#
#         # Signal any attached views that we are done inserting rows
#         self.endInsertRows()
#
#     modifiedChanged = qtc.pyqtSignal()
#     @qtc.pyqtProperty(bool, notify=modifiedChanged)
#     def modified(self):
#         """Return True if objects have been added to or removed from the model since the last apply(), or if any
#          of the objects in the model have been modified."""
#         # If the cached value is still valid, use it
#         if self._modified is not None:
#             return self._modified
#
#         # Compare the lists, then check the objects if necessary
#         if self._original != self._current:
#             self._modified = True
#         else:
#             for obj in self._current:
#                 if obj.modified:
#                     self._modified = True
#                     break
#
#         self._modified = self._modified or False
#         return self._modified
#
#     @qtc.pyqtSlot()
#     def apply(self):
#         """Save the current state of the model, and call apply() on all contained objects."""
#         was_modified = self._modified
#         self._modified = None
#
#         for obj in self._current:
#             obj.apply()
#
#         self._original = list(self._current)
#
#         if self.modified != was_modified:
#             self.modifiedChanged.emit()
#
#     @qtc.pyqtSlot()
#     def revert(self):
#         """Discard modifications to the model. Each object contained in the model has its revert() method called."""
#         was_modified = self._modified
#         self._modified = None
#
#         for obj in self._current:
#             obj.revert()
#
#         self._current = list(self._original)
#
#         if self.modified != was_modified:
#             self.modifiedChanged.emit()
#
#     @qtc.pyqtSlot(int, int, result=qtc.QModelIndex)
#     def index(self, row, col, parent=qtc.QModelIndex()):
#         """Return a model index for the given row and column."""
#         if row >= self.rowCount() or col >= self.columnCount():
#             return qtc.QModelIndex()
#
#         return self.createIndex(row, col, self[row])
#
#     @qtc.pyqtSlot(int, result=qtc.QModelIndex)
#     def parent(self, index):
#         """Return the parent QModelIndex of the given index. ObjectModel only supports list and table access,
#         so this function always returns an invalid index."""
#         return qtc.QModelIndex()
#
#     @qtc.pyqtSlot(result=int)
#     def rowCount(self, parent=qtc.QModelIndex()):
#         """Return the number of rows in the model."""
#         return len(self)
#
#     @qtc.pyqtSlot(result=int)
#     def columnCount(self, parent=qtc.QModelIndex()):
#         """Return the number of columns in the model."""
#         return len(self._column_names) or 1
#
#     @qtc.pyqtSlot(qtc.QModelIndex, int, result=qtc.QVariant)
#     def data(self, index, role=qtc.Qt.DisplayRole):
#         """If role matches one of the values provided by roleNames(), returns the value of that property for the
#         object specified by index. Otherwise, the property is looked up by both the row and column of the index."""
#         if not index.isValid():
#             return qtc.QVariant()
#
#         obj = self._current[index.row()]
#         if role not in self._role_to_prop and role not in self._ref_role_to_prop:
#             role = self._column_to_role[index.column()]
#
#         if role in self._role_to_prop:
#                 return getattr(obj, self._role_to_prop[role])
#         elif role in self._ref_role_to_prop:
#             return getattr(obj.ref, self._ref_role_to_prop[role])
#
#     def roleNames(self):
#         """Return a dictionary containing the indices and encoded role names of the roles this model recognizes.
#         The role names correspond to the pyqtProperty they modfiy."""
#         return {k: v.encode() for k, v in itertools.chain(self._role_to_prop.items(), self._ref_role_to_prop.items())}
#
#     @qtc.pyqtSlot(str, result=int)
#     def role(self, name):
#         """Return the role (int) with a given name."""
#         for r, n in itertools.chain(self._role_to_prop.items(), self._ref_role_to_prop.items()):
#             if n == name:
#                 return r
#         else:
#             return -1
#
#     @qtc.pyqtSlot(qtc.QVariant)
#     def setColumns(self, *args):
#         """Set the model's columns to the properties named in the arguments. If there are no arguments, ObjectModel
#         uses the names of the roles, in the order they appear; if the argument is a QVariant, it assumes this is a
#         javascript array passed from QML; otherwise, it assumes the arguments are the names of the properties to use
#         for the columns."""
#         if not args:
#             self._column_to_role = {col: role for col, role in enumerate(itertools.chain(self._role_to_prop.keys(),
#                                                                                          self._ref_role_to_prop.keys()))}
#             self._column_names = [prop for prop in itertools.chain(self._role_to_prop.values(),
#                                                                    self._ref_role_to_prop.values())]
#             return
#
#         names = args[0].toVariant() if isinstance(args[0], qtc.QVariant) else list(map(lambda a: str(a), args))
#         self._column_names = names
#
#         self._column_to_role = {}
#         for col, name in enumerate(names):
#             try:
#                 role = next(filter(lambda rn: rn[1] == name, itertools.chain(self._role_to_prop.items(),
#                                                                              self._ref_role_to_prop.items())))[0]
#             except:
#                 continue
#
#             self._column_to_role[col] = role
#
#     @qtc.pyqtSlot(str, result=int)
#     def fieldIndex(self, prop):
#         """Return the column for a given property name."""
#         try:
#             return self._column_names.index(prop)
#         except ValueError:
#             return -1
#
#     def _connect_to(self, obj):
#         """Connects to an object's property change signals."""
#         if obj is None:
#             return
#         elif isinstance(obj, self._type):
#             roles = self._role_to_prop
#             self._connect_to(getattr(obj, 'ref', None))
#         elif isinstance(obj, self._ref_type):
#             roles = self._ref_role_to_prop
#
#         for num, name in roles.items():
#             signal_name = name + 'Changed'
#
#             try:
#                 signal = getattr(obj, signal_name)
#             except AttributeError:
#                 continue
#
#             if roles is self._role_to_prop:
#                 # if name not in self._slot_partials:
#                 #     self._slot_partials[name] = self.onChildModified #lambda p=name: self.onChildModified(p)
#
#                 signal.connect(self.onChildModified) #self._slot_partials[name])
#
#             if roles is self._ref_role_to_prop:
#                 # if name not in self._ref_slot_partials:
#                 #     self._ref_slot_partials[name] = self.onChildRefModified #lambda p=name: self.onChildRefModified(p)
#
#                 signal.connect(self.onChildRefModified) #self._ref_slot_partials[name])
#
#     def _disconnect_from(self, obj):
#         """Disconnects from an object's property change signals."""
#         if obj is None:
#             return
#         elif isinstance(obj, self._type):
#             roles = self._role_to_prop
#         elif isinstance(obj, self._ref_type):
#             roles = self._ref_role_to_prop
#             self._disconnect_from(getattr(obj, 'ref', None))
#
#         for num, name in roles.items():
#             signal_name = name + 'Changed'
#
#             try:
#                 signal = getattr(obj, signal_name)
#                 signal.disconnect(self.onChildModified if roles is self._role_to_prop else self.onChildRefModified)
#             except (AttributeError, KeyError):
#                 continue
#
#     def onChildModified(self, role_name=None):
#         """Translates a child object's property change signal into a dataChanged signal, allowing views to react
#         automatically to property changes."""
#         sender = self.sender()
#
#         try:
#             row = self._copy.index(sender)      # Have to access parent data member directly (index() is overridden
#                                                 # by QAbstractItemModel)
#         except ValueError:
#             return
#
#         # try:
#         #     col = self._column_names.index(role_name)
#         # except ValueError:
#         #     col = 0
#         #
#         # roles = [r for r, p in self._role_to_prop.items() if p == role_name]
#         #
#         # index = self.createIndex(row, col)
#         # self.dataChanged.emit(index, index, roles)
#         index1 = self.createIndex(row, 0)
#         index2 = self.createIndex(row, self.columnCount() - 1)
#         self.dataChanged.emit(index1, index2)
#
#         before = self.modified
#         self._modified = None
#         if self.modified != before:
#             self.modifiedChanged.emit()
#
#     def onChildRefModified(self, role_name=None):
#         """Translates a referenced object's property change signals into dataChanged signals, allowing connected views
#         to update automatically."""
#         sender = self.sender()
#
#         for row, obj in enumerate(self):
#             if obj.ref is sender:
#                 break
#         else:
#             return
#
#         # try:
#         #     col = self._column_names.index(role_name)
#         # except ValueError:
#         #     col = 0
#         #
#         # roles = [r for r, p in self._ref_role_to_prop.items() if p == role_name]
#         #
#         # index = self.createIndex(row, col)
#         # self.dataChanged.emit(index, index, roles)
#         index1 = self.createIndex(row, 0)
#         index2 = self.createIndex(row, self.columnCount() - 1)
#         self.dataChanged.emit(index1, index2)
#
#         before = self.modified
#         self._modified = None
#         if self.modified != before:
#             self.modifiedChanged.emit()
#
#     @property
#     def document(self):
#         return [o.document for o in self._current]
#
#     @property
#     def deleted(self):
#         """Returns objects that have been deleted from the Model. This can behave strangely if an object with
#         the same id has been added to the list more than once."""
#         # The mess of stuff below is functionally equivalent to
#         # the following commented lines, but runs MUCH faster.
#         #
#         # [i for i in self._original if i not in self._copy]
#
#         original_ids = {id(o) for o in self._original}
#         copy_ids = {id(o) for o in self._current}
#         deleted_ids = original_ids - copy_ids
#         deleted_objs = [o for o in self._original if id(o) in deleted_ids]
#
#         return deleted_objs
#
#     @qtc.pyqtSlot(str, qtc.QVariant, result=int)
#     def matchOne(self, role_name, value):
#         """Return the index of the first item in the model where role_name equals value, or -1 if there are no
#         matches."""
#         for idx, item in enumerate(self):
#             try:
#                 model_value = getattr(item, role_name)
#             except AttributeError:
#                 continue
#
#             if model_value == value:
#                 return idx
#         else:
#             return -1
#
#     @qtc.pyqtSlot(str, result=qtc.QVariant)
#     def min(self, role_name):
#         """Returns the minimum of the values of role_name."""
#         if not len(self):
#             return None
#
#         values = [getattr(o, role_name, None) for o in self]
#         values = [v for v in values if v is not None]
#         return min(values)
#
#     @qtc.pyqtSlot(str, result=qtc.QVariant)
#     def max(self, role_name):
#         """Returns the maximum for the given role name. Values of None and missing attributes are ignored."""
#         if not len(self):
#             return None
#
#         values = [getattr(o, role_name, None) for o in self]
#         values = [v for v in values if v is not None]
#         return max(values)
#
#
# ########################################################################################################################
#
#
# def ObjectModelProperty(_type, key, **kwargs):
#     """Shorthand for using MapProperty to create an ObjectModel property."""
#     kwargs.pop('default', None)
#     default_set = kwargs.get('default_set', None)
#     default_set = default_set if default_set is not None else lambda self: ObjectModel(_type, parent=self)
#
#     return Property(ObjectModel,
#                     key,
#                     enforce_type=ObjectModel,
#                     convert_type=lambda self, value: ObjectModel(_type, objects=value, parent=self),
#                     default_set=default_set,
#                     **kwargs)
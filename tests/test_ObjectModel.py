import PyQt5.QtCore as qtcore
import bson

from unittest import main
from unittest.mock import Mock

from cupi.objectmodel import *
from tools import *

ENABLE_PROFILING = True


class TestObjectModel(TestCase):

    def setUp(self):
        self.model = ObjectModel(_type=GenericObject,
                                 objects=[GenericObject({'p1': random_string(), 'index': i}) for i in range(TOTAL_ELEMENTS)],
                                 listen=True,
                                 parent=None)

        self.model.dataChanged = Mock()

        if ENABLE_PROFILING:
            self.pr = cProfile.Profile()

    def tearDown(self):
        if ENABLE_PROFILING:
            try:
                p = pstats.Stats(self.pr)
            except TypeError:
                return

            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats(15)

    def start_profiling(self, title):
        if ENABLE_PROFILING:
            self.pr.enable()

    def stop_profiling(self):
        if ENABLE_PROFILING:
            self.pr.disable()

    def test_init(self):
        for i in range(TEST_SIZE):
            self.assertIs(self.model, self.model[random_idx()].parent())

    def test_setitem(self):
        o1, o2, o3 = GenericObject(), GenericObject(), GenericObject()
        elements = [GenericObject(data=random_string()) for i in range(TEST_SIZE)]

        self.start_profiling('__setitem__')

        for i in range(TEST_SIZE):
            self.model[random_idx()] = elements[i]

        self.model[0] = o1
        self.model[int(TOTAL_ELEMENTS / 2)] = o2
        self.model[TOTAL_ELEMENTS - 1] = o3

        self.stop_profiling()

        self.assertIs(o1, self.model[0])
        self.assertIs(self.model, o1.parent())
        self.assertIs(o2, self.model[int(TOTAL_ELEMENTS / 2)])
        self.assertIs(self.model, o2.parent())
        self.assertIs(o3, self.model[TOTAL_ELEMENTS - 1])
        self.assertIs(self.model, o3.parent())
        self.assertEqual(TEST_SIZE + 3, self.model.dataChanged.emit.call_count)

    def test_delitem(self):
        listener = Mock()
        self.model.rowsAboutToBeRemoved.connect(listener)

        temp_parent = qtcore.QObject()
        o1, o3 = self.model[0], self.model[TOTAL_ELEMENTS - 1]
        o3.setParent(temp_parent)

        random_idxs = [random.randint(0, TOTAL_ELEMENTS - TEST_SIZE - 3) for i in range(TEST_SIZE)]

        del self.model[TOTAL_ELEMENTS - 1]
        del self.model[0]

        for i in range(TEST_SIZE):
            self.start_profiling('__delitem__')
            del self.model[random_idxs[i]]
            self.stop_profiling()

        self.model.apply()

        self.assertIs(None, o1.parent())
        self.assertIs(temp_parent, o3.parent())
        self.assertEqual(TEST_SIZE + 2, listener.call_count)

    def test_insert(self):
        o1, o2 = GenericObject(), GenericObject()
        listener = Mock()
        random_idxs = [random.randint(1, TOTAL_ELEMENTS - 2) for i in range(TEST_SIZE)]
        new_elements = [GenericObject(data=random_string()) for i in range(TEST_SIZE)]
        self.model.rowsAboutToBeInserted.connect(listener)

        self.model.insert(0, o1)
        self.model.insert(TOTAL_ELEMENTS, o2)

        for i in range(TEST_SIZE):
            self.start_profiling('insert')
            self.model.insert(random_idxs[i], new_elements[i])
            self.stop_profiling()

        self.assertIs(o1, self.model[0])
        self.assertIs(self.model, o1.parent())
        self.assertIs(o2, self.model[TOTAL_ELEMENTS + TEST_SIZE])
        self.assertIs(self.model, o2.parent())
        self.assertEqual(TEST_SIZE + 2, listener.call_count)

    def test_append(self):
        new_elements = [GenericObject(data=random_string()) for i in range(TEST_SIZE)]
        listener = Mock()
        self.model.rowsAboutToBeInserted.connect(listener)

        for i in range(TEST_SIZE):
            self.start_profiling('append')
            self.model.append(new_elements[i])
            self.stop_profiling()

        self.assertEqual(TOTAL_ELEMENTS + TEST_SIZE, len(self.model))
        self.assertIs(new_elements[0], self.model[TOTAL_ELEMENTS])
        self.assertIs(new_elements[-1], self.model[-1])
        self.assertEqual(TEST_SIZE, listener.call_count)

    def test_remove_row(self):
        """Test the model's removeRow() method."""
        self.model.beginRemoveRows = Mock()
        self.model.endRemoveRows = Mock()
        obj = self.model[0]
        parent = Mock()

        self.model.removeRow(0, parent)

        self.assertEqual(len(self.model), TOTAL_ELEMENTS - 1)
        self.assertNotIn(obj, self.model)
        self.model.beginRemoveRows.assert_called_with(parent, 0, 0)
        self.model.endRemoveRows.assert_called_once()
        self.model.beginRemoveRows.reset_mock()
        self.model.endRemoveRows.reset_mock()

        obj = self.model[-1]

        self.model.removeRow(len(self.model) - 1, parent)

        self.assertEqual(len(self.model), TOTAL_ELEMENTS - 2)
        self.assertNotIn(obj, self.model)
        self.model.beginRemoveRows.assert_called_with(parent, TOTAL_ELEMENTS - 2, TOTAL_ELEMENTS - 2)
        self.model.endRemoveRows.assert_called_once()

        with self.assertRaises(IndexError):
            self.model.removeRow(TOTAL_ELEMENTS)

    def test_remove_rows(self):
        """Test the removeRows() method."""
        self.model.beginRemoveRows = Mock()
        self.model.endRemoveRows = Mock()
        objs = [self.model[i] for i in range(5)]
        parent = Mock()

        self.model.removeRows(0, 5, parent)

        self.assertEqual(len(self.model), TOTAL_ELEMENTS - 5)
        for o in objs:
            self.assertNotIn(o, self.model)

        self.model.beginRemoveRows.assert_called_with(parent, 0, 4)
        self.model.endRemoveRows.assert_called_once()

        with self.assertRaises(IndexError):
            self.model.removeRows(len(self.model) - 3, 5, parent)

    def test_apply(self):
        """Test the model's apply() method."""

        # Make some additions
        for i in range(1, int(TEST_SIZE / 2)):
            self.model.append(GenericObject(data=random_string()))

        # Make some deletions
        for i in range(1, int(TEST_SIZE / 2)):
            del self.model[random_idx()]

        # Make some edits
        for i in range(1, TEST_SIZE):
            self.model[random_idx()].setProperty('data', random_string())

        # Set a new parent; make sure this is preserved
        temp_parent = qtcore.QObject()
        o1 = self.model[TEST_SIZE]
        o1.setParent(temp_parent)
        del self.model[TEST_SIZE]

        o2 = self.model[TEST_SIZE - 1]
        del self.model[TEST_SIZE - 1]

        # Check that apply() is called on items that are still
        # in the model, and is NOT called on items that have been
        # deleted.
        o1.apply, o2.apply = Mock(), Mock()
        self.model[0].apply = Mock()

        # Start the operation
        self.start_profiling('apply()')
        self.model.apply()
        self.stop_profiling()

        # Test the results
        self.assertFalse(self.model.modified)
        self.assertNotIn(o1, self.model)
        self.assertNotIn(o2, self.model)
        self.assertIs(temp_parent, o1.parent())
        self.assertIsNone(o2.parent())
        o1.apply.assert_not_called()
        o2.apply.assert_not_called()
        self.model[0].apply.assert_not_called()

    def test_revert(self):
        """Test the model's revert() method."""
        temp_parent = qtcore.QObject()
        o1, o2 = GenericObject(parent=self.model), GenericObject()

        # Make some additions
        for i in range(1, TEST_SIZE):
            self.model.append(GenericObject(data=random_string()))

        # Make some deletions
        for i in range(1, TEST_SIZE):
            del self.model[random_idx() or 1]

        # Set a new parent, make sure this is preserved
        o1 = self.model[TEST_SIZE]
        del self.model[TEST_SIZE]

        o2 = GenericObject(data=random_string())
        self.model.append(o2)
        o2.setParent(temp_parent)

        o3 = GenericObject(data=random_string())
        self.model.append(o3)

        # Check that revert() is called on children who remain
        # in the model, and NOT on deleted children.
        o1.revert, o2.revert = Mock(), Mock()
        self.model[0].revert = Mock()

        # Run the test
        self.start_profiling('revert()')
        self.model.revert()
        self.stop_profiling()

        # Test the results
        self.assertFalse(self.model.modified)
        self.assertIn(o1, self.model)
        self.assertNotIn(o2, self.model)
        self.assertIs(self.model, o1.parent())
        self.assertIs(temp_parent, o2.parent())
        self.assertIs(o3.parent(), self.model)
        o1.revert.assert_not_called()
        o2.revert.assert_not_called()
        self.model[0].revert.assert_not_called()

    def test_index(self):
        index = self.model.index(0, 0)
        self.assertTrue(index.isValid())

        index = self.model.index(TOTAL_ELEMENTS + 1, 0)
        self.assertFalse(index.isValid())

    def test_parent(self):
        index = self.model.parent(None)
        self.assertFalse(index.isValid())

    def test_rowCount(self):
        self.assertEqual(TOTAL_ELEMENTS, self.model.rowCount())

    def test_columnCount(self):
        self.assertEqual(6, self.model.columnCount())

    def test_data(self):
        var = self.model.data(qtcore.QModelIndex(), qtcore.Qt.DisplayRole)
        self.assertIsInstance(var, qtcore.QVariant)
        self.assertFalse(var.isValid())

        for i in range(TEST_SIZE):
            index = self.model.createIndex(i, 0)
            self.assertTrue(index.isValid())

            prop_to_role = {p: r for r, p in self.model._role_to_prop.items()}

            self.assertEqual(False, self.model.data(index, prop_to_role['modified']))         # modified property
            self.assertEqual(self.model[i].p1, self.model.data(index, prop_to_role['p1']))
            self.assertEqual(self.model[i].p2, self.model.data(index, prop_to_role['p2']))
            self.assertEqual(self.model[i].p3, self.model.data(index, prop_to_role['p3']))

        for i in range(TEST_SIZE):
            for j in range(3, 6):
                index = self.model.createIndex(i, j)
                self.assertTrue(index.isValid())

                self.assertEqual(getattr(self.model[i], 'p%s' % (j-2)), self.model.data(index, qtcore.Qt.DisplayRole))

    def test_roleNames(self):
        roles = self.model.roleNames()

        self.assertEqual('modified'.encode(), roles[qtcore.Qt.UserRole + 2])
        self.assertEqual('p1'.encode(), roles[qtcore.Qt.UserRole + 3])
        self.assertEqual('p2'.encode(), roles[qtcore.Qt.UserRole + 4])
        self.assertEqual('p3'.encode(), roles[qtcore.Qt.UserRole + 5])

    def test_setColumns(self):
        self.model.setColumns()
        self.test_roleNames()

        self.model.setColumns('p3', 'modified')
        index = self.model.createIndex(random_idx(), 0)
        self.assertEqual('property 3', self.model.data(index, qtcore.Qt.DisplayRole))
        index = self.model.createIndex(random_idx(), 1)
        self.assertEqual(False, self.model.data(index, qtcore.Qt.DisplayRole))

    def test_fieldIndex(self):
        self.assertEqual(-1, self.model.fieldIndex('unknown'))
        self.assertEqual(2, self.model.fieldIndex('modified'))
        self.assertEqual(3, self.model.fieldIndex('p1'))

        self.model.setColumns('p3', 'modified')
        self.assertEqual(-1, self.model.fieldIndex('p1'))
        self.assertEqual(0, self.model.fieldIndex('p3'))
        self.assertEqual(1, self.model.fieldIndex('modified'))

    def test_connect_to(self):
        self.model.onChildModified = Mock()

        self.model[0].p1 = 'new value'

        self.assertEqual(2, self.model.onChildModified.call_count)
        self.model.onChildModified.assert_called_with('p1')

    def test_disconnect_from(self):
        self.model.onChildModified = Mock()
        self.model.dataChanged.emit = Mock()

        self.model._disconnect_from(self.model[0])
        self.model[0].p1 = 'this is silly'
        self.model.onChildModified.assert_not_called()
        self.model.dataChanged.emit.assert_not_called()

    def test_onChildModified(self):
        self.model.dataChanged.emit = Mock()

        def check_emit_parameters2(topleft, bottomright, roles):
            self.assertEqual(0, topleft.row())
            self.assertEqual(3, topleft.column())
            self.assertEqual(0, bottomright.row())
            self.assertEqual(3, bottomright.column())
            self.assertEqual([qtcore.Qt.UserRole + 3], roles)

        def check_emit_parameters1(topleft, bottomright, roles):
            self.assertEqual(0, topleft.row())
            self.assertEqual(2, topleft.column())
            self.assertEqual(0, bottomright.row())
            self.assertEqual(2, bottomright.column())
            self.assertEqual([qtcore.Qt.UserRole + 2], roles)
            self.model.dataChanged.emit = check_emit_parameters2

        self.model.dataChanged.emit = check_emit_parameters1

        self.model[0].p1 = 'consult the book of armaments!'

    def test_matchOne(self):
        for prop in ['p1', 'p2', 'p3']:
            oid = bson.ObjectId()
            obj = GenericObject()
            setattr(obj, prop, str(oid))
            idx = random_idx()
            self.model.insert(idx, obj)

            i = self.model.matchOne(prop, str(oid))
            self.assertEqual(i, idx)

        oid = bson.ObjectId()
        i = self.model.matchOne('p1', str(oid))
        self.assertEqual(i, -1)

if __name__ == '__main__':
    main()
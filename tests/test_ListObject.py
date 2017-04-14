from unittest.mock import Mock

from tools import *


class TestListObject(ProfilingTestCase):

    def setUp(self):
        super().setUp()

        self.elements = [random_element() for i in range(TOTAL_ELEMENTS)]
        self.elements[0] = GenericObject(data=random_string())
        self.elements[1] = GenericObject(data=random_string())
        self.list = ListObject(self.elements)
        self.list.modifiedChanged = Mock()

    def test_getitem(self):
        print('Profiling __getitem__():')

        for i in range(TEST_SIZE):
            idx = random_idx()

            self.profile.enable()
            obj = self.list[idx]
            self.profile.disable()

            self.assertIs(obj, self.elements[idx])

    def test_getitem_outofbounds(self):
        with self.assertRaises(IndexError):
            self.list[TOTAL_ELEMENTS + 1]

    def test_getitem_negative(self):
        print('Profiling __getitem__() with negative indices:')
        for i in range(TEST_SIZE):
            idx = -random_idx()

            self.profile.enable()
            obj = self.list[idx]
            self.profile.disable()

            self.assertIs(obj, self.elements[idx])

    def test_setitem(self):
        print('Profiling __setitem__():')

        self.list[0] = self.elements[0]
        self.assertFalse(self.list.modified)
        self.list.modifiedChanged.emit.assert_not_called()

        for i in range(TEST_SIZE):
            idx = random_idx()
            obj = GenericObject(p1='test setitem')

            self.profile.enable()
            self.list[idx] = obj
            self.profile.disable()

            self.assertIs(self.list[idx], obj)

        self.assertTrue(self.list.modified)
        self.list.modifiedChanged.emit.assert_called_once()

    def test_setitem_negative(self):
        print('Profiling __setitem__() with negative indices:')

        for i in range(TEST_SIZE):
            idx = -random_idx()
            obj = GenericObject(p1='test setitem')

            self.profile.enable()
            self.list[idx] = obj
            self.profile.disable()

            self.assertIs(obj, self.list[idx])

        self.assertTrue(self.list.modified)
        self.list.modifiedChanged.emit.assert_called_once()

    def test_setitem_reset(self):
        item = self.list[0]

        self.list[0] = random_element()
        self.assertTrue(self.list.modified)
        self.list.modifiedChanged.emit.assert_called_once()

        self.list[0] = item
        self.assertFalse(self.list.modified)
        self.assertEqual(2, self.list.modifiedChanged.emit.call_count)

    def test_setitem_outofbounds(self):
        with self.assertRaises(IndexError):
            self.list[TOTAL_ELEMENTS + 1] = GenericObject()

    def test_delitem(self):
        for i in range(TEST_SIZE):
            idx = random.randint(0, TEST_SIZE)

            self.profile.enable()
            del self.list[idx]
            self.profile.disable()

        del self.list[0]

        self.assertNotIn(self.elements[0], self.list)
        self.assertTrue(self.list.modified)
        self.list.modifiedChanged.emit.assert_called()

    def test_delitem_outofbounds(self):
        with self.assertRaises(IndexError):
            del self.list[TOTAL_ELEMENTS + 1]

    def test_insert(self):
        for i in range(TEST_SIZE):
            idx = random_idx()
            obj = GenericObject()

            self.profile.enable()
            self.list.insert(idx, obj)
            self.profile.disable()

            self.assertIs(obj, self.list[idx])

        self.assertTrue(self.list.modified)
        self.list.modifiedChanged.emit.assert_called_once()

    def test_apply(self):
        for i in range(TEST_SIZE):
            obj = GenericObject()
            self.list.append(obj)

        new = self.list[-1]

        deleted = self.list[1]
        deleted.apply = Mock()

        for i in range(TEST_SIZE):
            del self.list[1]

        self.assertNotIn(deleted, self.list)

        self.list[0].p1 = 'test value'

        self.profile.enable()
        self.list.apply()
        self.profile.disable()

        self.assertFalse(self.list.modified)
        self.assertIn(new, self.list)
        self.assertNotIn(deleted, self.list)
        deleted.apply.assert_not_called()

    def test_revert(self):
        for i in range(TEST_SIZE):
            obj = GenericObject()
            self.list.append(obj)

        new = self.list[-1]
        new.revert = Mock()

        deleted = self.list[1]
        deleted.revert = Mock()

        for i in range(TEST_SIZE):
            del self.list[1]

        self.list[0].p1 = 'test value'

        self.profile.enable()
        self.list.revert()
        self.profile.disable()

        self.assertFalse(self.list.modified)
        self.assertNotIn(new, self.list)
        new.revert.assert_not_called()
        self.assertIn(deleted, self.list)
        deleted.revert.assert_called()

    def test_document(self):
        lo = ListObject(['one',
                         'two',
                         ListObject(['three', 'four'])])

        doc = lo.document

        self.assertEqual(doc, ['one', 'two', ['three', 'four']])
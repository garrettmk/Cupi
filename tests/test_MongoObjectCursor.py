import unittest
import unittest.mock as mock

from cupi import *
from tools import *

ENABLE_PROFILING = True


class TestMongoObjectCursor(unittest.TestCase):

    def setUp(self):
        documents = [{'_type': 'GenericObject',
                      'p1': 'loaded p1',
                      'p2': 'loaded p2'},
                     {'data': 'some data'}]
        self.mock_cursor = mock.MagicMock()
        self.mock_cursor.__iter__ = mock.Mock(return_value=iter(documents))
        self.mock_cursor.count = mock.Mock(return_value=2)
        self.cursor = MongoObjectCursor(self.mock_cursor)

    def test_del(self):
        del self.cursor
        self.mock_cursor.close.assert_called_once()

    def test_iter(self):
        self.assertIs(self.cursor, iter(self.cursor))

    def test_magic_next(self):
        obj = next(self.cursor)

        self.assertIsInstance(obj, GenericObject)
        self.assertEqual('loaded p1', obj.p1)
        self.assertEqual('loaded p2', obj.p2)
        self.assertFalse(obj.modified)

        obj = next(self.cursor)
        self.assertTrue(type(obj) is MapObject)
        self.assertEqual('some data', obj.getValue('data'))

        with self.assertRaises(StopIteration):
            next(self.cursor)

    def test_len(self):
        self.assertEqual(len(self.cursor), self.mock_cursor.count())

    def test_next(self):
        obj = self.cursor.next()

        self.assertIsInstance(obj, GenericObject)
        self.assertEqual('loaded p1', obj.p1)
        self.assertEqual('loaded p2', obj.p2)
        self.assertFalse(obj.modified)

        obj = self.cursor.next()
        self.assertTrue(type(obj) is MapObject)
        self.assertEqual('some data', obj.getValue('data'))

        self.assertIsNone(self.cursor.next())

    def test_count(self):
        self.assertEqual(self.cursor.count, self.mock_cursor.count())

    def test_done(self):
        self.assertFalse(self.cursor.done)
        for i in self.cursor:
            pass
        self.assertTrue(self.cursor.done)

    def test_close(self):
        self.cursor.close()
        self.mock_cursor.close.assert_called_once()
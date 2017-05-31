from unittest import TestCase
from unittest.mock import Mock

from cupi import MapObject
from tools import GenericObject


class TestMapObject(TestCase):

    original = {'a': 1, 'b': 2, 'c': 3}

    def setUp(self):
        self.doc = MapObject(self.original)
        self.doc.modifiedChanged = Mock()

    def test_from_document(self):
        doc = {'_type': 'GenericObject', 'p1': 'first', 'data': 'second'}

        obj = MapObject.from_document(doc)

        self.assertIsInstance(obj, GenericObject)
        self.assertEqual(obj.p1, 'first')
        self.assertEqual(obj['data'], 'second')

        doc = {'_type': 'Unknown', 'data': 'first'}
        obj = MapObject.from_document(doc)

        self.assertIs(MapObject, type(obj))
        self.assertEqual(obj['data'], 'first')

        doc = {'p1': 'first'}
        obj = MapObject.from_document(doc, default_type=GenericObject, data='second')

        self.assertIs(GenericObject, type(obj))
        self.assertEqual(obj.p1, 'first')
        self.assertEqual(obj['data'], 'second')

    def test_subtype(self):
        self.assertIs(MapObject, MapObject.subtype('MapObject'))
        self.assertIs(MapObject, MapObject.subtype(MapObject))
        self.assertIs(GenericObject, MapObject.subtype('GenericObject'))
        self.assertIs(GenericObject, MapObject.subtype(GenericObject))

        with self.assertRaises(ValueError):
            MapObject.subtype('Unknown')

        with self.assertRaises(TypeError):
            MapObject.subtype(Mock)

    def test_getitem_nonexistant(self):
        with self.assertRaises(KeyError):
            self.doc['d']

    def test_getitem_deleted(self):
        self.doc._dels = ['d']
        with self.assertRaises(KeyError):
            self.doc['d']

    def test_getitem_mod(self):
        self.doc._mods = {'d': 4}
        self.assertEqual(self.doc['d'], 4)

    def test_getitem_map(self):
        self.assertEqual(self.doc['a'], 1)

    def test_setitem_original_nochange(self):
        self.doc['a'] = 1
        self.assertNotIn('a', self.doc._mods)
        self.assertNotIn('a', self.doc._dels)
        self.assertEqual(1, self.doc['a'])
        self.assertFalse(self.doc.modified)
        self.assertEqual(0, self.doc.modifiedChanged.emit.call_count)

    def test_setitem_original_newvalue(self):
        self.doc['b'] = 20
        self.assertIn('b', self.doc._mods)
        self.assertNotIn('b', self.doc._dels)
        self.assertEqual(20, self.doc['b'])
        self.assertTrue(self.doc.modified)
        self.assertEqual(1, self.doc.modifiedChanged.emit.call_count)

    def test_setitem_new(self):
        self.doc['d'] = 4
        self.assertIn('d', self.doc._mods)
        self.assertNotIn('d', self.doc._dels)
        self.assertEqual(4, self.doc['d'])
        self.assertTrue(self.doc.modified)
        self.assertEqual(1, self.doc.modifiedChanged.emit.call_count)

    def test_setitem_original_reset(self):
        self.doc['c'] = 30
        self.doc['c'] = 3
        self.assertNotIn('c', self.doc._mods)
        self.assertNotIn('c', self.doc._dels)
        self.assertEqual(3, self.doc['c'])
        self.assertFalse(self.doc.modified)
        self.assertEqual(2, self.doc.modifiedChanged.emit.call_count)

    def test_delitem_original(self):
        del self.doc['a']
        self.assertIn('a', self.doc._map)
        self.assertIn('a', self.doc._dels)
        self.assertNotIn('a', self.doc._mods)
        with self.assertRaises(KeyError):
            self.doc['a']
        self.assertTrue(self.doc.modified)
        self.assertEqual(1, self.doc.modifiedChanged.emit.call_count)

    def test_delitem_new(self):
        self.doc['d'] = 4
        del self.doc['d']
        self.assertNotIn('d', self.doc._map)
        self.assertNotIn('d', self.doc._mods)
        self.assertNotIn('d', self.doc._dels)
        with self.assertRaises(KeyError):
            self.doc['d']
        self.assertFalse(self.doc.modified)
        self.assertEqual(2, self.doc.modifiedChanged.emit.call_count)

    def test_delitem_nonexistant(self):
        with self.assertRaises(KeyError):
            del self.doc['z']

    def test_delitem_twice(self):
        del self.doc['a']
        with self.assertRaises(KeyError):
            del self.doc['a']

    def test_iter_unmodified(self):
        l1 = list(iter(self.doc))
        l2 = list(iter(self.original))
        self.assertEqual(l1, l2)

    def test_iter_modified(self):
        self.doc['d'] = 4
        self.doc['e'] = 5
        del self.doc['b']

        l1 = list(iter(self.doc))
        l2 = list(iter({'a': 1, 'c': 3, 'd': 4, 'e': 5}))

        self.assertEqual(l1, l2)

    def test_len(self):
        self.assertEqual(3, len(self.doc))

    def test_keys_unmodified(self):
        self.assertEqual(list(self.doc.keys()), ['a', 'b', 'c'])

    def test_keys_modified(self):
        self.doc['d'] = 4
        self.doc['e'] = 5
        del self.doc['b']

        l1 = list(self.doc.keys())
        l2 = ['a', 'c', 'd', 'e']

        self.assertEqual(l1, l2)

    def test_items_unmodified(self):
        for kv1, kv2 in zip(self.original.items(), self.doc.items()):
            self.assertEqual(kv1, kv2)

    def test_items_modified(self):
        self.doc['a'] = 5
        del self.doc['b']
        self.doc['d'] = 4

        d = dict(self.original)
        d['a'] = 5
        del d['b']
        d['d'] = 4

        for kv1, kv2 in zip(d.items(), self.doc.items()):
            self.assertEqual(kv1, kv2)

    def test_values_unmodified(self):
        l1 = self.original.values()
        l2 = self.doc.values()

        for v1, v2 in zip(l1, l2):
            self.assertEqual(v1, v2)

    def test_values_modified(self):
        self.doc['a'] = 5
        del self.doc['b']
        self.doc['d'] = 4

        for v1, v2 in zip(self.doc.values(), [5, 3, 4]):
            self.assertEqual(v1, v2)

    def test_getValue_original_unmodified(self):
        self.assertEqual(1, self.doc.getValue('a'))

    def test_getValue_original_modified(self):
        self.doc['a'] = 5
        self.assertEqual(5, self.doc.getValue('a'))

    def test_getValue_new(self):
        self.doc['d'] = 4
        self.assertEqual(4, self.doc.getValue('d'))

    def test_getValue_deleted(self):
        del self.doc['a']
        with self.assertRaises(KeyError):
            self.doc.getValue('a')

    def test_getValue_default(self):
        self.assertEqual(5, self.doc.getValue('z', default=5))
        self.assertNotIn('z', self.doc._map)
        self.assertNotIn('z', self.doc._mods)
        self.assertNotIn('z', self.doc._dels)

    def test_getValue_default_set(self):
        self.assertEqual(5, self.doc.getValue('z', default_set=5))
        self.assertNotIn('z', self.doc._map)
        self.assertIn('z', self.doc._mods)
        self.assertNotIn('z', self.doc._dels)

    def test_getValue_default_callable(self):
        f = Mock(return_value=10)
        self.assertEqual(10, self.doc.getValue('z', default=f))
        self.assertNotIn('z', self.doc._map)
        self.assertNotIn('z', self.doc._mods)
        self.assertNotIn('z', self.doc._dels)

    def test_getValue_default_set_callable(self):
        f = Mock(return_value=10)
        self.assertEqual(10, self.doc.getValue('z', default_set=f))
        self.assertNotIn('z', self.doc._map)
        self.assertIn('z', self.doc._mods)
        self.assertNotIn('z', self.doc._dels)

    def test_setValue_original(self):
        sig = Mock()
        self.doc.setValue('a', 5, sig)
        self.assertIn('a', self.doc._mods)
        self.assertEqual(5, self.doc['a'])
        sig.emit.assert_called()

    def test_setValue_new(self):
        sig = Mock()
        self.doc.setValue('d', 4, sig)
        self.assertIn('d', self.doc._mods)
        self.assertEqual(4, self.doc['d'])
        sig.emit.assert_called()

    def test_map(self):
        map = self.doc.map
        self.assertEqual(map, self.original)
        with self.assertRaises(TypeError):
            map['a'] = 5

    def test_mods(self):
        self.doc['a'] = 10
        self.doc['d'] = 4
        mods = self.doc.mods
        self.assertEqual(mods, {'a': 10, 'd': 4})
        with self.assertRaises(TypeError):
            mods['a'] = 5

    def test_dels(self):
        del self.doc['a']
        del self.doc['b']
        dels = self.doc.dels

        self.assertIn('a', dels)
        self.assertIn('b', dels)
        with self.assertRaises(TypeError):
            dels[0] = 5

    def test_apply(self):
        self.doc['a'] = 10
        self.doc['d'] = 4
        self.doc.apply()

        self.assertFalse(self.doc.modified)
        for kv1, kv2 in zip(self.doc, {'a': 10, 'b': 2, 'c': 3, 'd': 4}):
            self.assertEqual(kv1, kv2)
        self.doc.modifiedChanged.emit.assert_called()

    def test_revert(self):
        self.doc['a'] = 10
        self.doc['b'] = 4
        self.doc.revert()

        self.assertFalse(self.doc.modified)
        for kv1, kv2 in zip(self.doc, {'a': 1, 'b': 2, 'c': 3}):
            self.assertEqual(kv1, kv2)
        self.doc.modifiedChanged.emit.assert_called()

    def test_document(self):
        mo = MapObject({'one': 1, 'two': 2, 'three': MapObject({'four': 4})})
        doc = mo.document

        self.assertEqual(doc, {'one': 1, 'two': 2, 'three': {'four': 4}})





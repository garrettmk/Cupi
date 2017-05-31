from unittest import TestCase

from PyQt5.QtCore import pyqtSignal

from cupi.objects import MapObject, Property


class MapObjectSubclass(MapObject):
    p2Notify = pyqtSignal()
    p3Notify = pyqtSignal()

    p1 = Property(int, 'p1')
    p2 = Property(int, 'p2', notify=p2Notify)
    p3 = Property(int, 'p3', notify=p3Notify, default=5)
    p4 = Property(int, 'p4', default_set=10)
    property_name = Property(str, 'prop_name')


class TestMapObjectSubclass(TestCase):

    def setUp(self):
        self.obj = MapObjectSubclass(p1=1, property_name='beep boop beep')

    def test_init(self):
        self.assertEqual(self.obj.property_name, 'beep boop beep')
        self.assertIn('prop_name', self.obj)

    def test_property_get(self):
        self.assertEqual(1, self.obj.p1)

    def test_property_set(self):
        self.obj.p1 = 10

        self.assertEqual(10, self.obj.p1)
        self.assertEqual(10, self.obj['p1'])
        self.assertTrue(self.obj.modified)

    def test_property_notify(self):
        self.obj.p2 = 22

        self.assertEqual(22, self.obj.p2)
        self.assertEqual(22, self.obj['p2'])
        self.assertTrue(self.obj.modified)
        #self.assertEqual(1, self.obj.p2Notify.emit.call_count)

    def test_property_default(self):
        self.assertEqual(5, self.obj.p3)
        self.assertNotIn('p3', self.obj._map)
        self.assertNotIn('p3', self.obj._mods)
        self.assertNotIn('p3', self.obj._dels)

    def test_property_default_set(self):
        self.assertEqual(10, self.obj.p4)
        self.assertNotIn('p4', self.obj._map)
        self.assertIn('p4', self.obj._mods)
        self.assertNotIn('p4', self.obj._dels)

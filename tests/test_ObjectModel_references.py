import PyQt5.QtCore as qtc
from unittest import main
from unittest.mock import Mock
from cupi.objectmodel import *
from tools import *


class TestObjectModelRefs(TestCase):

    def setUp(self):
        self.model = ObjectModel(_type=GenericObjectReference,
                                 objects=[GenericObjectReference(ref=GenericObject({'p1': random_string()})) \
                                          for i in range(TOTAL_ELEMENTS)])

    def test_data(self):
        variant = self.model.data(qtc.QModelIndex(), qtc.Qt.DisplayRole)
        self.assertIsInstance(variant, qtc.QVariant)
        self.assertFalse(variant.isValid())

        for i in range(TEST_SIZE):
            index = self.model.createIndex(i, 0)
            self.assertTrue(index.isValid())

            prop_to_role = {p: r for r, p in self.model._ref_role_to_prop.items()}

            self.assertEqual(False, self.model.data(index, prop_to_role['modified']))
            self.assertEqual(self.model[i].ref.p1, self.model.data(index, prop_to_role['p1']))
            self.assertEqual(self.model[i].ref.p2, self.model.data(index, prop_to_role['p2']))
            self.assertEqual(self.model[i].ref.p3, self.model.data(index, prop_to_role['p3']))

    def test_connect_to(self):
        # Test signals from content objects
        self.model.onChildModified = Mock()
        self.model.onChildRefModified = Mock()

        self.model[0].autoLoad = True

        self.assertEqual(1, self.model.onChildModified.call_count)
        self.assertEqual(0, self.model.onChildRefModified.call_count)

        # Test signals from referenced objects
        self.model.onChildModified.reset_mock()
        self.model.onChildRefModified.reset_mock()

        self.model[0].ref.p1 = random_string()

        self.assertEqual(0, self.model.onChildModified.call_count)
        self.assertEqual(2, self.model.onChildRefModified.call_count)

from unittest.mock import Mock, MagicMock
from cupi.mongodatabase import *
from tools import *


class TestMongoObjectReference(TestCase):

    def setUp(self):
        self.obj = GenericObject(data=random_string(), _id=random_string())
        self.ref = MongoObjectReference(item=self.obj)

    def test_item_getter(self):
        item = self.ref.item
        self.assertIs(item, self.obj)

    def test_item_setter(self):
        obj = GenericObject(_id=random_string())

        self.ref.item = obj

        self.assertIs(obj, self.ref.item)

    def test_referencedId(self):
        self.assertEqual(self.ref.referencedId, self.obj['_id'])

    def test_referencedType(self):
        self.assertEqual(self.ref.referencedType, GenericObject.__name__)

    def test_autoLoad(self):
        self.ref.autoLoad = True
        self.assertTrue(self.ref.autoLoad)


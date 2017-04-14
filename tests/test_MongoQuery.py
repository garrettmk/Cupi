from cupi.mongodatabase import MongoQuery
from tools import *


class TestMongoQuery(TestCase):

    def setUp(self):
        self.query = MongoQuery()

    def test_filterByValue(self):
        self.query.filterByValue('p1', 5)

        self.assertEqual(self.query.query.document, {'p1': 5})

    def test_getFilterValue(self):
        self.query.filterByValue('p1', 5)
        self.assertEqual(self.query.getFilterValue('p1'), 5)
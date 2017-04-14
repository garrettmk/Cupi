import PyQt5.QtCore as qtcore
from unittest.mock import Mock, MagicMock
from cupi import mongodatabase
from cupi import *
from tools import *

ENABLE_PROFILING = True


class TestMongoDatabase(TestCase):

    def setUp(self):
        # Set up a mock client, database, and collection
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_collection = Mock()
        self.collection_names = ['coll_one', 'coll_2', 'coll_3']

        # Set up their relationships
        self.mock_client.__getitem__.return_value = self.mock_db
        self.mock_db.__getitem__.return_value = self.mock_collection
        self.mock_db.collection_names = Mock(return_value=self.collection_names)

        # Mock out pymongo.MongoClient() to provide our mocked objects
        mongodatabase.pymongo.MongoClient = Mock(return_value=self.mock_client)

        self.db = MongoDatabase()

    def test_escaped(self):
        """Test character escaping on a tree of mixed objects."""
        doc = {'$query': {'.abc': ['$one', '.two'], 'def': '$ghi'}}
        expected = {'＄query': {'．abc': ['$one', '.two'], 'def': '$ghi'}}
        escaped = self.db.escaped(doc)

        self.assertEqual(escaped, expected)

    def test_unescaped(self):
        """Test character unescaping on a tree of mixed objects."""
        doc = {'＄query': {'．abc': ['$one', '.two'], 'def': '$ghi'}}
        expected = {'$query': {'.abc': ['$one', '.two'], 'def': '$ghi'}}
        unescaped = self.db.unescaped(doc)

        self.assertEqual(unescaped, expected)

    def test_updates(self):
        """Test the ability to create an update document from a tree of mixed objects."""
        mo = MapObject({'one': 1, 'two': [1, 2], 'three': {'four': 4, 'five': [1, 2, 3, 4, 5]}})
        mo['one'] = 11
        mo['two'].append(3)
        del mo['three']['four']
        mo['three']['five'][4] = 'five'
        expected = {'$set': {'one': 11, 'two.2': 3, 'three.five.4': 'five'},
                    '$unset': {'three.four': None}}

        self.assertEqual(expected, MongoDatabase._updates(mo))

    def test_listobject_updates(self):
        """Test making an update document for a ListObject."""
        lo = ListObject([1, 2, ['three', 'four'], 5, 6])
        del lo[1]
        del lo[2]
        expected = {'$set': {'': [1, ['three', 'four'], 6]}}

        self.assertEqual(expected, MongoDatabase._listobject_updates(lo))

        lo = ListObject([1, 2, ['three', 'four'], 5, 6])
        lo[0] = 'one'
        lo[2][0] = 3
        expected = {'$set': {'0': 'one', '2.0': 3}}

        self.assertEqual(expected, MongoDatabase._listobject_updates(lo))

        lo = ListObject([1, 2, ['three', 'four'], 5, 6])
        lo.append(7)
        lo[2].append(8)
        expected = {'$set': {'5': 7, '2.2': 8}}

        self.assertEqual(expected, MongoDatabase._listobject_updates(lo))

    def test_mapobject_updates(self):
        """Test making an update document from a MapObject."""
        mo = MapObject({'a': 1, 'b': 2, 'c': {'d': 4, 'e': 5}})
        del mo['a']
        mo['b'] = 22
        del mo['c']['e']
        mo['f'] = MapObject({'g': 7})
        expected = {'$set': {'b': 22, 'f': {'g': 7}}, '$unset': {'a': None, 'c.e': None}}

        self.assertEqual(expected, MongoDatabase._mapobject_updates(mo))

    def test_statusMessage(self):
        """Test that changing the status message sends out the appropriate signals."""
        self.db.statusMessageChanged = Mock()

        self.db.statusMessage = 'Test One'
        self.assertEqual(1, self.db.statusMessageChanged.emit.call_count)
        self.assertEqual('Test One', self.db.statusMessage)

        self.db.statusMessage = 'Test Two'
        self.assertEqual(2, self.db.statusMessageChanged.emit.call_count)

    def test_uri(self):
        """Test the uri property."""
        self.assertEqual('', self.db.uri)
        with self.assertRaises(AttributeError):
            self.db.uri = 'Test'

    def test_collectionNames(self):
        """Test that collection names have been retrieved properly and a QStringListModel has been created."""
        self.db.connect('test')
        names = self.db.collectionNames

        self.assertIsInstance(names, qtcore.QStringListModel)
        self.assertEqual(names.stringList(), self.collection_names)

    def test_connect(self):
        """Test the behavior of the connect() method."""
        self.db.uriChanged = Mock()
        self.db.collectionNamesChanged = Mock()
        self.db.connectedChanged = Mock()

        self.db.connect('testdb')

        mongodatabase.pymongo.MongoClient.assert_called_once_with('mongodb://localhost:27017/')
        self.mock_client.__getitem__.assert_called_once_with('testdb')
        self.db.uriChanged.emit.assert_called_once()
        self.db.collectionNamesChanged.emit.assert_called_once()
        self.db.connectedChanged.emit.assert_called_once()

        self.db.connect('testdb', 'testuri')
        self.mock_client.close.assert_called_once()
        mongodatabase.pymongo.MongoClient.assert_called_with('testuri')

    def test_disconnect(self):
        """Test the behavior of the disconnect() method."""
        self.db.connect('test')

        self.db.uriChanged = Mock()
        self.db.connectedChanged = Mock()
        self.db.collectionNamesChanged = Mock()

        self.db.disconnect()

        self.mock_client.close.assert_called_once()
        self.db.connectedChanged.emit.assert_called_once()
        self.db.uriChanged.emit.assert_called_once()
        self.db.collectionNamesChanged.emit.assert_called_once()
        self.assertEqual('', self.db.uri)
        self.assertEqual(0, self.db.collectionNames.rowCount())

    def test_getObject(self):
        """Test the getObject() method."""
        search_doc = {'field': 'filter'}
        sort_doc = {'sort': 'value'}
        query = MongoQuery(query=search_doc, sort=sort_doc)

        obj_doc = {'data': random_string()}
        self.mock_collection.find_one = Mock(return_value=obj_doc)
        self.db._db = self.mock_db

        obj = self.db.getObject('GenericObject', query)

        self.mock_collection.find_one.assert_called_with(search_doc, modifiers={'$orderby': sort_doc})
        self.assertIsInstance(obj, GenericObject)
        self.assertEqual(obj['data'], obj_doc['data'])

    def test_getCursor(self):
        """Test the getCursor() method."""
        self.db.connect('test')

        with self.assertRaises(ValueError):
            self.db.getCursor('some type')

        with self.assertRaises(TypeError):
            self.db.getCursor(int)

        query = MongoQuery(query={'field': 'filter'}, sort={'field': 1})
        mongodatabase.MongoObjectCursor = Mock()

        mock_parent = Mock()
        cursor = self.db.getCursor(GenericObject, query, parent=mock_parent)

        self.mock_db.__getitem__.assert_called_with(GenericObject.__collection__)
        self.mock_collection.find.assert_called_with({'field': 'filter'},
                                                modifiers={'$orderby': {'field': 1}},
                                                no_cursor_timeout=True)
        mongodatabase.MongoObjectCursor.assert_called_with(self.mock_collection.find(),
                                                           database=self.db,
                                                           default_type=GenericObject,
                                                           parent=mock_parent)

    def test_saveObject(self):
        obj = GenericObject(data='abcdefg')
        doc = obj.document

        mock_result = Mock()
        mock_result.inserted_id = 'test id'
        self.mock_collection.insert_one = Mock(return_value=mock_result)
        self.db.connect('test')

        result = self.db.saveObject(obj)

        self.assertTrue(result)
        self.mock_db.__getitem__.assert_called_with(GenericObject.__collection__)
        self.assertEqual('test id', obj['_id'])
        self.mock_collection.insert_one.assert_called_with(doc)

        obj.p1 = 'modified'
        obj['q'] = MongoQuery(query={'field': 'filter'})
        expected = {'$set': {'p1': 'modified',
                             'q': {'＄query': {'field': 'filter'}, '_type': 'MongoQuery'}}}

        result = self.db.saveObject(obj)

        self.assertTrue(result)
        self.mock_collection.update.assert_called_with({'_id': 'test id'}, expected, upsert=True)
        self.assertFalse(obj.modified)
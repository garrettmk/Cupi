import pytest
import datetime
import cupi as qp
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq
import unittest.mock as mock


########################################################################################################################


class MapObjectSubclass(qp.MapObject):
    """Used for testing MapObject and MapProperty."""
    testProperty = qp.Property(str, 'test_property')

    notifyPropertyChanged = qtc.pyqtSignal()
    notifyProperty = qp.Property(bool, 'notify_property', notify=notifyPropertyChanged)

    defaultProperty = qp.Property(str, 'default_property', default='default string')
    defaultSetProperty = qp.Property(str, 'default_set_property', default_set='default_set string')
    readOnlyProperty = qp.Property(str, 'read_only_property', read_only=True, default='read only string')

    objectProperty = qp.MapObjectProperty(qp.MapObject, 'object_property')
    listProperty = qp.ListProperty('list_property')
    datetimeProperty = qp.DateTimeProperty('datetime_property')


class SubclassReference(qp.MapObjectReference):
    """Used for testing MapObjectReference."""
    referent_type = 'MapObjectSubclass'


########################################################################################################################

TEST_DOC = {'static': 1,
            'modded': 2,
            'deleted': 3,
            'object': None,
            '_id': 'test_id'}

MOD_DOC = {'static': 1,
           'modded': '2.0',
           'object': None,
           '_id': 'test_id'}

@pytest.fixture
def mock_object():
    return mock.MagicMock(spec=qp.MapObject, modified=False, document={})

@pytest.fixture
def clean_map(mock_object):
    """This fixture provides a fresh, unedited MapObject."""
    TEST_DOC['object'] = mock_object
    mo = qp.MapObject(TEST_DOC)
    mo.modifiedChanged = mock.Mock()
    assert not mo.modified
    return mo

@pytest.fixture
def dirty_map(mock_object):
    """This fixture provides a MapObject that has had a key deleted and a key changed. """
    TEST_DOC['object'] = mock_object
    MOD_DOC['object'] = mock_object
    mo = qp.MapObject(TEST_DOC)
    mo.modifiedChanged = mock.Mock()

    for key, value in TEST_DOC.items():
        if key not in MOD_DOC:
            del mo[key]
        elif value != MOD_DOC[key]:
            mo[key] = MOD_DOC[key]

    assert mo.modified
    assert mo.modifiedChanged.emit.call_count == 1

    return mo

@pytest.fixture(params=['clean', 'dirty'])
def mixed_map(request, clean_map, dirty_map):
    """Provided for tests that are the same for clean and edited maps."""
    if request.param == 'clean':
        return clean_map
    elif request.param == 'dirty':
        return dirty_map

@pytest.fixture
def mapobject_subclass():
    return MapObjectSubclass(notifyProperty='test value')


########################################################################################################################


def test_metaclass():
    assert 'MapObject' in qp.MapObjectMetaclass.subclasses
    assert 'MapObjectSubclass' in qp.MapObjectMetaclass.subclasses
    for _type in [qp.MapObject, MapObjectSubclass]:
        for prop in [name for name in dir(_type) if type(getattr(_type, name)) is qtc.pyqtProperty]:
            assert prop in qp.MapObjectMetaclass.properties[_type.__name__]


########################################################################################################################


def test_init_parent():
    """Check that the object provided by the keyword argument 'parent' is provided to the QObject constructor."""
    parent = qtc.QObject()
    test_object = qp.MapObject(parent=parent)
    assert test_object.parent() is parent

    test_object = qp.MapObject(parent=None)
    assert test_object.parent() is None


def test_init_with_document():
    """Create a MapObject using a dictionary."""
    test_object = qp.MapObject(TEST_DOC)
    for key, value in TEST_DOC.items():
        assert test_object[key] == value
    assert not test_object.modified


def test_init_with_properties():
    """Check that properties can be assigned using keyword arguments to the constructor."""
    test_object = qp.MapObject(id='test string')
    # '_id' is used by the property setter, not 'id'
    assert 'id' not in test_object
    assert test_object.id == 'test string'
    assert test_object.modified


def test_init_with_keywords(mock_object):
    """Check that keyword arguments, except 'parent' and keywords that match property names, are stored in the
    map as key-value pairs."""
    TEST_DOC['object'] = mock_object
    test_object = qp.MapObject(**TEST_DOC)
    assert not test_object.modified
    for key, value in TEST_DOC.items():
        assert key in test_object
        assert test_object[key] == value

    assert 'object' in test_object
    test_object['object'].setParent.assert_called_with(test_object)
    test_object['object'].modifiedChanged.connect.assert_called_once()


def test_connect(mixed_map):
    """Check that _connect() sets the object's parent and connects to it's modifiedChanged signal."""
    mock_object = mock.Mock(spec=qp.MapObject)
    mixed_map._connect(mock_object)
    mock_object.setParent.assert_called_with(mixed_map)
    mock_object.modifiedChanged.connect.assert_called_with(mixed_map.modifiedChanged)


def test_disconnect(mixed_map):
    """Check that _disconnect() sets the object's parent to None and disconnects from the modifiedChanged signal."""
    mock_object = mock.Mock(spec=qp.MapObject)
    mixed_map._disconnect(mock_object)
    mock_object.setParent.assert_called_with(None)
    mock_object.modifiedChanged.disconnect.assert_called_with(mixed_map.modifiedChanged)


def test_getitem_valid(clean_map):
    """Check that __getitem__() can retrieve a value for a valid key."""
    assert clean_map['static'] == TEST_DOC['static']


def test_getitem_invalid(mixed_map):
    """Check that __getitem__() throws a KeyError exception when used with a nonexistent key."""
    with pytest.raises(KeyError):
        mixed_map['bad key']


def test_getitem_modified(dirty_map):
    """Check that __getitem__() correctly retrieves modified keys."""
    assert dirty_map['modded'] == '2.0'


def test_getitem_deleted(dirty_map):
    """Check that __getitem__() throws a KeyError when accessing a deleted key."""
    with pytest.raises(KeyError):
        dirty_map['deleted']


def test_setitem_exists(mixed_map):
    """Check that __setitem__() can modify keys."""
    mock_object = mock.Mock(spec=qp.MapObject)
    mixed_map['modded'] = mock_object
    assert mixed_map['modded'] is mock_object
    mock_object.setParent.assert_called_with(mixed_map)
    mock_object.modifiedChanged.connect.assert_called_with(mixed_map.modifiedChanged)


def test_setitem_new(mixed_map):
    """Check that __setitem__() can create new keys."""
    mock_object = mock.Mock(spec=qp.MapObject)
    mixed_map['new key'] = mock_object
    assert mixed_map['new key'] == mock_object
    mock_object.setParent.assert_called_with(mixed_map)
    mock_object.modifiedChanged.connect.assert_called_with(mixed_map.modifiedChanged)


def test_setitem_reset(clean_map):
    """Check that __setitem__() can restore deleted keys."""
    assert not clean_map.modified
    del clean_map['deleted']
    assert clean_map.modified
    assert 'deleted' not in clean_map
    clean_map['deleted'] = TEST_DOC['deleted']
    assert not clean_map.modified


def test_delitem(mixed_map):
    """Check that __delitem__() can delete unmodified keys."""
    del mixed_map['modded']
    assert 'modded' not in mixed_map


def test_delitem_nonexistent(mixed_map):
    """Check that __delitem__() raises KeyError when given a nonexistent key."""
    with pytest.raises(KeyError):
        del mixed_map['bad key']


def test_delitem_twice(dirty_map):
    """Check that __delitem__() raises KeyError when used twice on the same key."""
    with pytest.raises(KeyError):
        del dirty_map['deleted']


def test_getValue_valid(mixed_map):
    """Check that getValue() can retrieve values from the map."""
    assert mixed_map.getValue('static') == 1


def test_getValue_invalid(mixed_map):
    """Check that getValue() throws an KeyError when given an invalid key."""
    with pytest.raises(KeyError):
       assert mixed_map.getValue('bad key')


def test_getValue_modded(dirty_map):
    """Check that getValue() correctly retrieves modified values."""
    assert dirty_map['modded'] == '2.0'


def test_getValue_deleted(dirty_map):
    """Check that getValue() raises KeyError when retrieving a key that has been deleted."""
    with pytest.raises(KeyError):
        dirty_map['deleted']


def test_getValue_default(mixed_map):
    """Check that getValue() returns the given default value when provided key is not in the map."""
    assert mixed_map.getValue('bad key', default='cool') == 'cool'
    assert 'bad key' not in mixed_map


def test_getValue_default_callable(mixed_map):
    """Check that getValue() uses a given callable to provide the default value."""
    default_mock = mock.Mock(return_value=5)
    assert mixed_map.getValue('bad key', default=default_mock) == 5
    assert default_mock.called


def test_getValue_default_set(mixed_map):
    """Check that getValue() inserts the default value into the map, if the provided key is not already there."""
    assert mixed_map.getValue('new key', default_set='cool') == 'cool'
    assert 'new key' in mixed_map and mixed_map['new key'] == 'cool'


def test_getValue_default_set_callable(mixed_map):
    """Check that getValue() uses a given callable to provide a default value for a missing key."""
    default_mock = mock.Mock(return_value=5)
    assert mixed_map.getValue('new key', default_set=default_mock) == 5
    assert default_mock.called
    assert 'new key' in mixed_map and mixed_map['new key'] == 5


def test_getValue_enforce_type(mixed_map):
    """Check that getValue() will convert the value type if the enforce_type keyword is given."""
    assert mixed_map.getValue('modded', enforce_type=float) == 2.0
    assert type(mixed_map['modded']) is float


def test_getValue_enforce_type_with_convert(mixed_map):
    """Check the getValue() uses a given convert function when enforcing types."""
    convert_mock = mock.Mock(return_value=1.234)
    assert mixed_map.getValue('modded', enforce_type=float, convert_type=convert_mock) == convert_mock.return_value
    assert convert_mock.called
    assert mixed_map.getValue('modded') == convert_mock.return_value
    assert convert_mock.call_count == 1


def test_setValue_exists(mixed_map):
    """Test setValue() on an existing key."""
    mixed_map.setValue('key1', 10)
    assert mixed_map['key1'] == 10


def test_setValue_nonexistent(mixed_map):
    """Test setValue() on a key that doesn't already exist in the map."""
    mixed_map.setValue('keyX', 'x')
    assert 'keyX' in mixed_map
    assert mixed_map['keyX'] == 'x'


def test_setValue_with_signal(mixed_map):
    """Test setValue() with a notify signal."""
    mock_signal = mock.Mock()
    mixed_map.setValue('key1', 10, mock_signal)
    assert mixed_map['key1'] == 10
    assert mock_signal.emit.called


def test_setValue_QJSValue(mixed_map):
    """Test the setValue() properly handles a QJSValue (as would be given by QML)."""
    test_value = qtq.QJSValue(123)
    mixed_map.setValue('key1', test_value)
    assert type(mixed_map['key1']) is int
    assert mixed_map['key1'] == 123


def test_iter_clean(clean_map):
    """Check that __iter__() gives us an iterator for the map's keys."""
    assert list(iter(clean_map)) == list(TEST_DOC)


def test_iter_dirty(dirty_map):
    assert list(iter(dirty_map)) == list(MOD_DOC)


def test_len(clean_map):
    """Check that using len() works correctly."""
    assert len(clean_map) == len(TEST_DOC)


def test_items_clean(clean_map):
    """Check that items() gives us a valid iterator."""
    assert list(clean_map.items()) == list(TEST_DOC.items())


def test_items_dirty(dirty_map):
    assert list(dirty_map.items()) == list(MOD_DOC.items())


def test_values_clean(clean_map):
    """Check that values() gives us an iterator for the map's values."""
    assert list(clean_map.values()) == list(TEST_DOC.values())


def test_values_dirty(dirty_map):
    assert list(dirty_map.values()) == list(MOD_DOC.values())


def test_modified_clean(clean_map):
    """Test the modified property."""
    assert not clean_map.modified


def test_modified_dirty(dirty_map):
    assert dirty_map.modified


def test_apply_dirty(dirty_map):
    """Test the apply() method."""
    dirty_map.apply()
    assert not dirty_map.modified
    assert dirty_map.modifiedChanged.emit.call_count == 2
    assert list(dirty_map.items()) == list(MOD_DOC.items())


def test_revert(dirty_map):
    """Test the revert() method."""
    dirty_map.revert()
    assert not dirty_map.modified
    assert dirty_map.modifiedChanged.emit.call_count == 2
    assert list(dirty_map.items()) == list(TEST_DOC.items())


def test_document_clean(clean_map):
    """Test the document() method."""
    doc = dict(TEST_DOC)
    doc['object'] = doc['object'].document
    assert clean_map.document == doc


def test_document_dirty(dirty_map):
    doc = dict(MOD_DOC)
    doc['object'] = doc['object'].document
    assert dirty_map.document == doc


def test_id_getter(mixed_map):
    """Test the id property getter."""
    assert mixed_map.id == 'test_id'


def test_id_setter(mixed_map):
    """Test the id property setter."""
    mixed_map.id = 'new id'
    assert mixed_map.id == 'new id'


def test_hasid(mixed_map):
    """Test the hasId() method."""
    assert mixed_map.hasId
    del mixed_map['_id']
    assert not mixed_map.hasId


def test_from_document():
    """Test the from_document() class method."""
    test_object = qp.MapObject.from_document(TEST_DOC, extra='foo')
    for key, value in TEST_DOC.items():
        assert test_object[key] == value
    assert test_object['extra'] == 'foo'


def test_subclass():
    """Test the _subclass() class method."""
    assert qp.MapObject._subclass('MapObjectSubclass') is MapObjectSubclass
    assert qp.MapObject._subclass(MapObjectSubclass) is MapObjectSubclass
    with pytest.raises(ValueError):
        qp.MapObject._subclass('farts')
    with pytest.raises(TypeError):
        qp.MapObject._subclass(str)


def test_all_subclass_names():
    """Test the _all_subclass_names() class method."""
    assert 'MapObjectSubclass' in qp.MapObject._all_subclass_names()


def test_takes_ownership(mixed_map, mapobject_subclass):
    """Check that MapObject takes ownership of other MapObject and ObjectModel objects when they are added to it."""
    assert mixed_map.parent() is None
    mapobject_subclass.objectProperty = mixed_map
    assert mapobject_subclass.objectProperty is mixed_map
    assert mixed_map.parent() is mapobject_subclass


########################################################################################################################


def test_property(mapobject_subclass):
    """Test that the Property function creates a valid pyqtProperty."""
    # The property has not been set yet, so accessing it should raise an exception
    with pytest.raises(KeyError):
        mapobject_subclass.testProperty

    # Set and get
    mapobject_subclass.testProperty = 'check'
    assert mapobject_subclass.testProperty == 'check'


def test_notify_property(mapobject_subclass):
    """Test that property change signals are emitted when Property is used with the notify keyword."""
    mock_slot = mock.Mock()
    mapobject_subclass.notifyPropertyChanged.connect(mock_slot)
    mapobject_subclass.notifyProperty = True
    assert mock_slot.call_count == 1


def test_default_property(mapobject_subclass):
    """Test that default values are provided when Property is used with the default keyword."""
    assert mapobject_subclass.defaultProperty == 'default string'
    assert 'default_property' not in mapobject_subclass


def test_default_set_property(mapobject_subclass):
    """Test that default values are set when Property is used with the default_set keyword."""
    assert 'default_set_property' not in mapobject_subclass
    assert mapobject_subclass.defaultSetProperty == 'default_set string'
    assert 'default_set_property' in mapobject_subclass


def test_read_only_property(mapobject_subclass):
    """Test that attempting to set a property created with the read_only parameter throws an exception."""
    with pytest.raises(AttributeError):
        mapobject_subclass.readOnlyProperty = 'foo'


def test_mapobject_property(mapobject_subclass):
    """Test the MapObjectProperty convenience function."""
    assert 'object_property' not in mapobject_subclass
    obj = mapobject_subclass.objectProperty
    assert 'object_property' in mapobject_subclass
    assert isinstance(obj, qp.MapObject)
    assert obj.parent() is mapobject_subclass


def test_list_property(mapobject_subclass):
    """Test the ListProperty convenience function."""
    assert 'list_property' not in mapobject_subclass
    obj = mapobject_subclass.listProperty
    assert 'list_property' in mapobject_subclass
    assert isinstance(obj, list)


def test_datetime_property(mapobject_subclass):
    """Test the DateTimeProperty convenience function."""
    # Test the default behavior
    assert 'datetime_property' not in mapobject_subclass
    obj = mapobject_subclass.datetimeProperty
    assert 'datetime_property' in mapobject_subclass
    assert isinstance(obj, datetime.datetime)
    assert obj == datetime.datetime.fromtimestamp(0, datetime.timezone.utc)

    # Assign the property to a QDateTime object, and check that it is correctly converted to a datetime
    qtime = qtc.QDateTime.fromTime_t(1434600360, qtc.Qt.OffsetFromUTC, -28800)
    mapobject_subclass.datetimeProperty = qtime

    obj = mapobject_subclass.datetimeProperty
    assert isinstance(obj, datetime.datetime)
    assert obj == datetime.datetime.fromtimestamp(1434600360, datetime.timezone(datetime.timedelta(hours=-8)))


########################################################################################################################


def test_reference_metaclass():
    """Test MapObjectReferenceMetaclass."""
    ref_attrs = dir(SubclassReference)

    for prop_name in qp.MapObjectMetaclass.properties['MapObjectSubclass']:
        assert prop_name in ref_attrs
        assert prop_name + 'Changed' in ref_attrs


def test_reference(clean_map):
    """Test the MapObjectReference object."""
    ref = qp.MapObjectReference()

    # Check the defaults
    assert ref.referentId is None
    assert ref.referentType == 'MapObject'
    assert ref.autoLoad is False

    # Assign an object
    ref.ref = clean_map
    assert ref.referentType == 'MapObject'
    assert ref.referentId == TEST_DOC['_id']
    assert ref.ref is clean_map


def test_reference_subclass(mapobject_subclass):
    """Test SubclassReference."""
    ref = SubclassReference()

    with pytest.raises(AttributeError):
        ref.notifyProperty

    ref.ref = mapobject_subclass
    assert ref.ref is mapobject_subclass
    assert ref.notifyProperty == 'test value'
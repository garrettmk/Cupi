import pytest
import datetime
import itertools
import cupi as qp
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq
import unittest.mock as mock


########################################################################################################################


class MapObjectSubclass(qp.MapObject):
    """Used for testing MapObject and MapProperty."""
    testProperty = qp.Property('test_property', str)

    notifyPropertyChanged = qtc.pyqtSignal()
    notifyProperty = qp.Property('notify_property', bool, notify=notifyPropertyChanged)

    defaultProperty = qp.Property('default_property', str, default='default string')
    defaultSetProperty = qp.Property('default_set_property', str, default_set='default_set string')
    readOnlyProperty = qp.Property('read_only_property', str, read_only=True, default='read only string')

    objectProperty = qp.MapObjectProperty('object_property')
    listProperty = qp.ListProperty('list_property')
    datetimeProperty = qp.DateTimeProperty('datetime_property')


class SubclassReference(qp.MapObjectReference):
    """Used for testing MapObjectReference."""
    referent_type = 'MapObjectSubclass'


########################################################################################################################


STATIC_KEY = 'static'
MODDED_KEY = 'modded'
DELETED_KEY = 'deleted'
OBJECT_KEY = 'object'
ID_KEY = '_id'
INVALID_KEY = 'aadsfsadfas'

TEST_DOC = {STATIC_KEY: 1.414,
            MODDED_KEY: 2.718,
            DELETED_KEY: 3.14,
            OBJECT_KEY: None,
            ID_KEY: 'test_id'}


@pytest.fixture(params=['clean', 'modded'])
def mapobject_and_doc(request):
    """Provides a MapObject in several different states."""
    # Create a fake object and put it in the global documents
    TEST_DOC[OBJECT_KEY] = mock.MagicMock(spec=qp.MapObject, modified=False, document={})
    expected = dict(TEST_DOC)

    mo = qp.MapObject(TEST_DOC)
    mo.modifiedChanged = mock.MagicMock()

    if request.param == 'clean':
        pass
    elif request.param == 'modded':
        mo[MODDED_KEY] = '2.0'
        expected[MODDED_KEY] = '2.0'

        del mo[DELETED_KEY]
        del expected[DELETED_KEY]

    return (mo, expected)

@pytest.fixture
def mock_object():
    return mock.MagicMock(spec=qp.MapObject, modified=False, document={})

@pytest.fixture
def mapobject_subclass():
    return MapObjectSubclass(notifyProperty='test value')


########################################################################################################################


def test_mapobject_metaclass():
    """Test that MapObjectMetaclass is discovering subclasses and pyqtProperties."""
    assert 'MapObject' in qp.MapObjectMetaclass.subclasses
    assert 'MapObjectSubclass' in qp.MapObjectMetaclass.subclasses
    for _type in [qp.MapObject, MapObjectSubclass]:
        for prop in [name for name in dir(_type) if type(getattr(_type, name)) is qtc.pyqtProperty]:
            assert prop in qp.MapObjectMetaclass.properties[_type.__name__]


########################################################################################################################


@pytest.mark.parametrize('parent', [True, None])
@pytest.mark.parametrize('document', ['as doc', 'as keywords', None])
@pytest.mark.parametrize('properties', [{'id': 'id value'}, None])
@mock.patch('cupi.objects.MapObject._connect')
def test_init(mock_connect, document, properties, parent):
    """Test MapObject.__init__() with various combinations of arguments."""
    test_args = []
    test_kwargs = {}
    expected_doc = dict(TEST_DOC)

    # Build the args, kwargs, and expected result for the test call
    if parent:
        test_kwargs['parent'] = qtc.QObject()

    if document == 'as doc':
        test_args.append(TEST_DOC)
    elif document == 'as keywords':
        test_kwargs.update(TEST_DOC)
    else:
        expected_doc = {}

    if properties is not None:
        test_kwargs.update(properties)
        expected_doc['_id'] = 'id value'

    # Make the test call
    test_object = qp.MapObject(*test_args, **test_kwargs)

    # Check that the map object matches the document
    assert len(test_object) == len(expected_doc)
    for key, value in expected_doc.items():
        assert test_object[key] == value

    # If no properties were specified, the map should be in an unmodified state
    if properties is None:
        assert not test_object.modified
    else:
        assert test_object.id == 'id value'

    # Check that _connect was called on all elements
    for value in expected_doc.values():
        assert mock.call(value) in mock_connect.call_args_list

    # Check that the object's parent is set correctly
    if parent:
        assert test_object.parent() is test_kwargs['parent']
    else:
        assert test_object.parent() is None


@pytest.mark.parametrize('obj', [None,
                                 mock.Mock(),
                                 mock.Mock(spec=qp.MapObject),
                                 mock.Mock(spec=qp.ObjectModel),
                                 mock.Mock(spec=MapObjectSubclass)])
def test_connect(mapobject_and_doc, obj):
    """Test the _connect() helper method."""
    mapobject, expected = mapobject_and_doc

    # Do the test call
    mapobject._connect(obj)

    # Check that valid objects were re-parented and connected to
    # Everything else should be ignored.
    if isinstance(obj, (qp.MapObject, qp.ObjectModel)):
        obj.setParent.assert_called_with(mapobject)
        obj.modifiedChanged.connect.assert_called_with(mapobject.modifiedChanged)
    elif obj is not None:
        assert not obj.method_calls


@pytest.mark.parametrize('obj', [None,
                                 mock.Mock(),
                                 mock.Mock(spec=qp.MapObject),
                                 mock.Mock(spec=qp.ObjectModel),
                                 mock.Mock(spec=MapObjectSubclass)])
def test_disconnect(mapobject_and_doc, obj):
    """Test the _disconnect() helper method."""
    mapobject, expected = mapobject_and_doc

    # Do the test call
    mapobject._disconnect(obj)

    # Check that valid objects were disconnected and de-parented
    # Everything else should be ignored.
    if isinstance(obj, (qp.MapObject, qp.ObjectModel)):
        obj.setParent.assert_called_with(None)
        obj.modifiedChanged.disconnect.assert_called_with(mapobject.modifiedChanged)
    elif obj is not None:
        assert not obj.method_calls


def test_getitem(mapobject_and_doc):
    """Test the __getitem__() method."""
    mapobject, expected = mapobject_and_doc

    for key in TEST_DOC:
        if key in expected:
            assert mapobject[key] == expected[key]
        else:
            with pytest.raises(KeyError):
                mapobject[key]


@pytest.mark.parametrize('key', [MODDED_KEY, DELETED_KEY, OBJECT_KEY])
@mock.patch('cupi.objects.MapObject._connect')
@mock.patch('cupi.objects.MapObject._disconnect')
def test_setitem(mock_disconnect, mock_connect, mapobject_and_doc, mock_object, key):
    """Test the __setitem__() method."""
    mapobject, expected = mapobject_and_doc
    was_modified = expected != TEST_DOC

    # Do the test call
    mapobject[key] = mock_object
    assert mapobject[key] is mock_object

    # If the map wasn't already modified, it should be modified now
    if not was_modified:
        assert mapobject.modified
        assert mapobject.modifiedChanged.emit.called_once

    # The map should connect to new objects
    assert mock.call(mock_object) in mock_connect.call_args_list

    # If the new value replaces an object, the map should disconnect from it
    if key == OBJECT_KEY:
        assert mock.call(expected[key]) in mock_disconnect.call_args_list


@pytest.mark.parametrize('key', [MODDED_KEY, DELETED_KEY, OBJECT_KEY, INVALID_KEY])
@mock.patch('cupi.objects.MapObject._disconnect')
def test_delitem(mock_disconnect, mapobject_and_doc, key):
    """Test the __delitem__() method."""
    mapobject, expected = mapobject_and_doc
    was_modified = expected != TEST_DOC

    # Do the test call
    if key in expected:
        del mapobject[key]
    else:
        with pytest.raises(KeyError):
            del mapobject[key]

    with pytest.raises(KeyError):
        mapobject[key]

    # If the map wasn't modified before, it should be now
    if not was_modified and key != INVALID_KEY:
        assert mapobject.modified
        assert mapobject.modifiedChanged.emit.called_once

    # Deleted objects should be disconnected
    if key == OBJECT_KEY:
        assert mock.call(expected[key]) in mock_disconnect.call_args_list


@pytest.mark.parametrize('key', [MODDED_KEY, DELETED_KEY, INVALID_KEY])
@pytest.mark.parametrize('default', [3, lambda self: 3, None])
@pytest.mark.parametrize('default_set', [True, False, None])
@pytest.mark.parametrize('enforce_type,convert_type', [(str, None),
                                                       (str, lambda s, v: str(v)),
                                                       (None, None)])
def test_getvalue(mapobject_and_doc, key, default, default_set, enforce_type, convert_type):
    """Test the getValue() method."""
    mapobject, expected = mapobject_and_doc
    test_kwargs = {}

    # Build the test call arguments
    if default is not None:
        test_kwargs['default'] = default

    if default_set is not None:
        test_kwargs['default_set'] = default_set

    if enforce_type is not None:
        test_kwargs['enforce_type'] = enforce_type

    if convert_type is not None:
        test_kwargs['convert_type'] = convert_type

    # Determine the value that should be returned
    if key in expected:
        expected_value = expected[key]
    elif default is not None:
        expected_value = default(mapobject) if callable(default) else default
    else:
        expected_value = None

    if enforce_type is not None:
        expected_value = enforce_type(expected_value)

    # Do the test call
    if key in expected or default is not None:
        returned_value = mapobject.getValue(key, **test_kwargs)
    else:
        with pytest.raises(KeyError):
            mapobject.getValue(key)
        return

    assert returned_value == expected_value

    # Check that default_set was used correctly
    if default_set is True \
            and default is not None \
            and key not in expected:
        assert key in mapobject
        assert mapobject[key] == expected_value


@pytest.mark.parametrize('key', [MODDED_KEY, DELETED_KEY, OBJECT_KEY, INVALID_KEY])
@pytest.mark.parametrize('value', [42, qtq.QJSValue(42), mock.MagicMock(spec=qp.MapObject),
                                   mock.MagicMock(spec=qp.ObjectModel)])
@pytest.mark.parametrize('mock_signals', [[], [mock.Mock()], [mock.Mock(), mock.Mock()]])
def test_setvalue(mapobject_and_doc, key, value, mock_signals):
    """Test the setValue() method."""
    mapobject, expected = mapobject_and_doc

    mapobject.setValue(key, value, *mock_signals)

    if isinstance(value, qtq.QJSValue):
        assert mapobject[key] == value.toVariant()
    else:
        assert mapobject[key] == value

    for sig in mock_signals:
        assert sig.emit.called_once


def test_iter(mapobject_and_doc):
    """Test the __iter__() method."""
    mapobject, expected = mapobject_and_doc
    assert list(iter(mapobject)) == list(expected)


def test_len(mapobject_and_doc):
    """Test the __len__() method."""
    mapobject, expected = mapobject_and_doc
    assert len(mapobject) == len(expected)


def test_items(mapobject_and_doc):
    """Test the items() method."""
    mapobject, expected = mapobject_and_doc
    assert list(mapobject.items()) == list(expected.items())


def test_values(mapobject_and_doc):
    """Test the values() method."""
    mapobject, expected = mapobject_and_doc
    assert list(mapobject.values()) == list(expected.values())


def test_modified(mapobject_and_doc):
    """Test the modified property."""
    mapobject, expected = mapobject_and_doc

    if expected == TEST_DOC:
        assert not mapobject.modifiedChanged.emit.called
        assert not mapobject.modified
    else:
        assert mapobject.modifiedChanged.emit.called
        assert mapobject.modified


@pytest.mark.parametrize('method', ['apply', 'revert'])
def test_apply_revert(mapobject_and_doc, method):
    """Test the apply() and revert() methods."""
    mapobject, expected = mapobject_and_doc
    was_modified = expected != TEST_DOC
    mapobject.modifiedChanged.emit.reset_mock()

    if method == 'apply':
        expected_result = expected
        mapobject.apply()
    elif method == 'revert':
        expected_result = TEST_DOC
        mapobject.revert()

    assert not mapobject.modified
    assert len(mapobject) == len(expected_result)
    if was_modified:
        assert mapobject.modifiedChanged.emit.called_once

    for key in expected_result:
        assert mapobject[key] == expected_result[key]


def test_document(mapobject_and_doc):
    """Test the document property."""
    mapobject, expected = mapobject_and_doc
    expected[OBJECT_KEY] = expected[OBJECT_KEY].document

    assert mapobject.document == expected


@pytest.mark.parametrize('_type', [None, 'MapObjectSubclass'])
@pytest.mark.parametrize('default_type', [None, MapObjectSubclass, 'MapObjectSubclass'])
@pytest.mark.parametrize('extra_kwargs', [None, {'test_property': 'foo'}])
def test_from_document(_type, default_type, extra_kwargs):
    """Test the from_document() class method."""
    test_kwargs = {}
    doc = dict(TEST_DOC)
    expected = dict(doc)

    # Build the arguments for the test call, and determine the expected result
    if _type is not None:
        doc['_type'] = _type
        expected['_type'] = _type

    if default_type is not None:
        test_kwargs['default_type'] = default_type
        expected['_type'] = 'MapObjectSubclass'

    if extra_kwargs is not None:
        test_kwargs.update(extra_kwargs)
        expected.update(extra_kwargs)

    # Make the test call
    return_value = qp.MapObject.from_document(doc, **test_kwargs)

    # Make sure we get back a MapObject subclass in an unmodified state
    if _type is not None or default_type is not None:
        assert isinstance(return_value, MapObjectSubclass)
    else:
        assert isinstance(return_value, qp.MapObject)

    assert not return_value.modified
    assert len(return_value) == len(expected)
    for key in expected:
        assert return_value[key] == expected[key]


@pytest.mark.parametrize('_type', [None, 'invalid', 'MapObject', qp.MapObject, 'MapObjectSubclass', MapObjectSubclass])
def test_subclass(_type):
    """Test the _subclass() class method."""
    if _type is None or _type == 'invalid':
        with pytest.raises(ValueError):
            qp.MapObject._subclass(_type)
    elif _type == 'MapObject' or _type is qp.MapObject:
        assert qp.MapObject._subclass(_type) is qp.MapObject
    elif _type == 'MapObjectSubclass' or _type is MapObjectSubclass:
        assert qp.MapObject._subclass(_type) is MapObjectSubclass


def test_all_subclass_names():
    """Test the _all_subclass_names() class method."""
    assert 'MapObjectSubclass' in qp.MapObject._all_subclass_names()


########################################################################################################################

@pytest.mark.parametrize('_type', [int, float, str, qp.MapObject, MapObjectSubclass])
@pytest.mark.parametrize('default', ['default value', None])
@pytest.mark.parametrize('default_set', [True, False, None])
@pytest.mark.parametrize('fget', ['fget value', None])
@pytest.mark.parametrize('fset', ['fset value', None])
@pytest.mark.parametrize('read_only', [True, False, None])
@pytest.mark.parametrize('enforce_type', ['enforce value', None])
@pytest.mark.parametrize('convert_type', ['convert_value', None])
@pytest.mark.parametrize('notify', [True, None])
@mock.patch('cupi.objects.MapObject.getValue')
@mock.patch('cupi.objects.MapObject.setValue')
@mock.patch('PyQt5.QtCore.pyqtProperty', return_value='new pyqtProperty')
def test_property(mock_property, mock_setvalue, mock_getvalue, _type, default, default_set, fget, fset, read_only,
                  enforce_type, convert_type, notify):
    """Test the Property convenience function."""
    # Build a dictionary of keyword arguments so that we can filter out None's
    if notify is not None:
        notify_mock = mock.Mock()
        notify_mock.__get__ = mock.Mock(return_value='notify signal')
    else:
        notify_mock = None

    test_kwargs = {'default': default,
                   'default_set': default_set,
                   'fget': fget,
                   'fset': fset,
                   'read_only': read_only,
                   'notify': notify_mock,
                   'enforce_type': enforce_type,
                   'convert_type': convert_type}
    test_kwargs = {k: v for k, v in test_kwargs.items() if v is not None}

    # Call the function under test
    return_value = qp.Property('test_key',
                               _type,
                               **test_kwargs)

    # Gather data
    prop_args = mock_property.call_args[0]
    prop_kwargs = mock_property.call_args[1]
    getter = prop_kwargs.pop('fget')
    setter = prop_kwargs.pop('fset')

    # Check that _type was passed along properly
    assert prop_args == (_type,)

    # If fget was provided, check that it was passed to pyqtProperty
    # If not, analyze the behavior of the generated fget function
    if fget is not None:
        assert getter is fget
    else:
        # Call the generated getter so we can analyze how it calls getValue()
        getter('self')
        getter_args = mock_getvalue.call_args[0]
        getter_kwargs = mock_getvalue.call_args[1]

        # Check that self and key were used correctly
        assert getter_args == ('self', 'test_key')

        # Check the keyword arguments
        if default is not None:
            assert 'default' in getter_kwargs
            assert getter_kwargs.pop('default') is default
        else:
            assert 'default' not in getter_kwargs

        if default_set is not None:
            assert 'default_set' in getter_kwargs
            assert getter_kwargs.pop('default_set') is default_set
        else:
            assert 'default_set' not in getter_kwargs

        if enforce_type is not None:
            assert 'enforce_type' in getter_kwargs
            assert getter_kwargs.pop('enforce_type') is enforce_type
        else:
            assert 'enforce_type' not in getter_kwargs

        if convert_type is not None:
            assert 'convert_type' in getter_kwargs
            assert getter_kwargs.pop('convert_type') is convert_type

        # Make sure there are no other arguments
        assert not len(getter_kwargs)

    # If fset was provided, check that it was passed to pyqtProperty
    # If not, analyze the behavior of the generated fset function
    if fset is not None and read_only is not True:
        assert setter is fset
    elif read_only is True:
        assert setter is None
    elif fset is None and read_only is not True:
        # Call the generated fset function so we can analyze how it calls setValue()
        setter('self', 'set value')
        setter_args = mock_setvalue.call_args[0]
        setter_kwargs = mock_setvalue.call_args[1]

        # Check the keyword arguments
        if notify is not None:
            assert prop_kwargs['notify'] is test_kwargs['notify']
            assert setter_args == ('self', 'test_key', 'set value', 'notify signal')
        else:
            assert setter_args == ('self', 'test_key', 'set value')

        # There should be no keyword arguments for the setter
        assert not len(setter_kwargs)

    # If notify was given, check that it got passed to pyqtProperty
    if notify is not None:
        assert 'notify' in prop_kwargs
        assert prop_kwargs['notify'] is prop_kwargs['notify']

    # Check that pyqtProperty return value was returned from Property
    assert return_value is mock_property.return_value


@pytest.mark.parametrize('test_func', [qp.MapObjectProperty, qp.ObjectModelProperty, qp.ListProperty, qp.DateTimeProperty])
@pytest.mark.parametrize('_type', [qp.MapObject, MapObjectSubclass, None])
@pytest.mark.parametrize('default', ['default value', None])
@pytest.mark.parametrize('default_set', [True, False, None])
@pytest.mark.parametrize('notify', ['notify value', None])
@pytest.mark.parametrize('fget', ['fget value', None])
@pytest.mark.parametrize('fset', ['fset value', None])
@mock.patch('cupi.objects.Property')
def test_property_convenience_functions(mock_property, test_func, _type, default, default_set, notify, fget, fset):
    """Test the MapObjectProperty, ListProperty, and DateTimeProperty convenience functions."""
    # Build a dictionary of arguments, and expected results
    test_kwargs = {'default': default,
                   'default_set': default_set,
                   'notify': notify,
                   'fget': fget,
                   'fset': fset}
    test_kwargs = {k: v for k, v in test_kwargs.items() if v is not None}
    test_args = ['test_key']

    expected_args = list(test_args)
    expected_kwargs = dict(test_kwargs)

    # Modify for individual test methods
    if test_func is qp.MapObjectProperty:
        if _type is not None:
            test_kwargs['_type'] = _type
            expected_args.append(_type)
        else:
            expected_args.append(qp.MapObject)
        expected_kwargs['enforce_type'] = expected_args[-1]

    if test_func is qp.ObjectModelProperty:
        if _type is not None:
            test_kwargs['_type'] = _type

        expected_args.append(qp.ObjectModel)
        expected_kwargs['enforce_type'] = qp.ObjectModel

    elif test_func is qp.ListProperty:
        expected_args.append(qtc.QVariant)
        expected_kwargs['enforce_type'] = list

    elif test_func is qp.DateTimeProperty:
        expected_args.append(qtc.QDateTime)
        expected_kwargs['enforce_type'] = datetime.datetime

    else:
        assert True, 'Unhandled test case'

    # Make the call
    return_value = test_func(*test_args, **test_kwargs)

    # Gather data
    prop_args = mock_property.call_args[0]
    prop_kwargs = mock_property.call_args[1]

    # MapObjectProperty and ObjectModelProperty uses a default lambda, so check for that
    if test_func is qp.MapObjectProperty:
        if default is None:
            default_value = prop_kwargs.pop('default')
            assert callable(default_value)
            assert type(default_value('self')) is expected_args[-1]

        if default_set is None:
            assert prop_kwargs.pop('default_set') is True

    if test_func is qp.ObjectModelProperty:
        if default is None:
            default_value = prop_kwargs.pop('default')
            assert callable(default_value)

        if default_set is None:
            assert prop_kwargs.pop('default_set') is True

    # Check the args and kwargs
    assert prop_args == tuple(expected_args)
    assert len(prop_kwargs) == len(expected_kwargs) + 1

    for key in expected_kwargs:
        assert prop_kwargs[key] == expected_kwargs[key]

    # Check the return value
    assert return_value is mock_property.return_value

    # Check the convert_type functions
    if test_func is qp.MapObjectProperty:
        test_doc = {'test_property': 'this is a test'}
        mo = prop_kwargs['convert_type']('self', test_doc)
        assert isinstance(mo, expected_args[1])
        for k, v in test_doc.items():
            assert mo[k] == v

    elif test_func is qp.ListProperty:
        test_doc = [1, 2, 3, 4, 5]
        mo = prop_kwargs['convert_type']('self', test_doc)
        assert isinstance(mo, list)
        for mo_item, test_item in itertools.zip_longest(mo, test_doc):
            assert mo_item == test_item

    elif test_func is qp.DateTimeProperty:
        qtime = qtc.QDateTime(qtc.QDate(2015, 6, 18),
                              qtc.QTime(4, 6),
                              qtc.Qt.OffsetFromUTC,
                              -28800)
        test_time = prop_kwargs['convert_type']('self', qtime)
        assert isinstance(test_time, datetime.datetime)
        assert test_time.tzinfo is datetime.timezone.utc
        assert test_time.timestamp() == qtime.toTime_t()


########################################################################################################################


def test_reference_metaclass():
    """Test MapObjectReferenceMetaclass."""
    ref_attrs = dir(SubclassReference)

    for prop_name in qp.MapObjectMetaclass.properties['MapObjectSubclass']:
        assert prop_name in ref_attrs
        assert prop_name + 'Changed' in ref_attrs


def test_reference(mapobject_and_doc):
    """Test the MapObjectReference object."""
    mapobject, expected = mapobject_and_doc
    ref = qp.MapObjectReference()

    # Check the defaults
    assert ref.referentId is None
    assert ref.referentType == 'MapObject'
    assert ref.autoLoad is False

    # Assign an object
    ref.ref = mapobject
    assert ref.referentType == 'MapObject'
    assert ref.referentId == TEST_DOC['_id']
    assert ref.ref is mapobject


def test_reference_subclass(mapobject_subclass):
    """Test SubclassReference."""
    ref = SubclassReference()
    mock_slot = mock.Mock()

    with pytest.raises(AttributeError):
        ref.notifyProperty

    ref.ref = mapobject_subclass
    assert ref.ref is mapobject_subclass
    assert ref.notifyProperty == 'test value'

    ref.notifyPropertyChanged.connect(mock_slot)
    ref.notifyProperty = 'new value'
    assert mock_slot.call_count == 1

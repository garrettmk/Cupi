import itertools
import pytest
import cupi as qp
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq
import unittest.mock as mock


########################################################################################################################


class GenericObject(qp.MapObject):

    genericPropertyChanged = qtc.pyqtSignal()
    genericProperty = qp.Property('generic_property', str, notify=genericPropertyChanged)


########################################################################################################################


@pytest.fixture(params=[True, False])
def init_parent(request):
    if request.param is True:
        return qtc.QObject()
    else:
        return None


@pytest.fixture(params=[True, False])
def init_objects(request):
    if request.param is True:
        return model_objects()
    else:
        return None


@pytest.fixture
def model_objects():
    return [GenericObject({'generic_property': 'omg'}) for i in range(10)]


@pytest.fixture
def model(model_objects):
    m = qp.ObjectModel(GenericObject, model_objects)
    m.modifiedChanged = mock.Mock()
    m.dataChanged = mock.Mock()
    return m


########################################################################################################################


@pytest.mark.parametrize('_type', [GenericObject, 'GenericObject', qp.MapObjectReference])
@pytest.mark.parametrize('listen', [False, True])
@mock.patch('cupi.ObjectModel._connect_to')
def test_init(mock_connect, _type, init_objects, listen, init_parent):
    """Test the ObjectModel __init__ method."""
    model = qp.ObjectModel(_type=_type, objects=init_objects, listen=listen, parent=init_parent)

    # Check that the parent is set correctly
    assert qtc.QObject.parent(model) is init_parent

    # Check that the model took ownership of the objects
    if init_objects is not None:
        for obj in model:
            assert obj.parent() is model

    # Check that property roles were correctly discovered
    type_class = qp.MapObject._subclass(_type)
    props = [prop for prop in dir(type_class) if isinstance(getattr(type_class, prop), qtc.pyqtProperty)]
    for name in model.roleNames().values():
        assert name.decode() in props
    for prop in props:
        assert prop.encode() in model.roleNames().values()

    # Check that columns are set up correctly
    assert model.columnCount() == len(props)
    for name in model.columnNames():
        assert name in props
    for prop in props:
        assert prop in model.columnNames()

    # Check that property change signals have been connected to correctly
    if init_objects is not None:
        for obj in init_objects:
            if listen:
                mock_connect.assert_called_with(obj)
            else:
                assert obj not in mock_connect.call_args_list

    # The model should be in an 'unmodified' state
    assert not model.modified


########################################################################################################################


def test_getitem(model, model_objects):
    """Test the __getitem__() method."""
    for idx, obj in enumerate(model_objects):
        assert obj is model[idx]

    with pytest.raises(IndexError):
        model[999]


@mock.patch('cupi.ObjectModel._connect_to')
@mock.patch('cupi.ObjectModel._disconnect_from')
def test_setitem(mock_disconnect, mock_connect, model, model_objects):
    """Test the __setitem__() method."""
    new_obj = GenericObject()
    old_obj = model[5]

    model[5] = new_obj

    mock_disconnect.assert_called_with(old_obj)
    mock_connect.assert_called_with(new_obj)
    assert model[5] is new_obj
    assert old_obj.parent() is None
    assert new_obj.parent() is model
    assert model.modified
    assert model.modifiedChanged.emit.called
    assert model.dataChanged.emit.called


@mock.patch('cupi.ObjectModel.removeRows')
def test_delitem(mock_remove, model):
    """Test the __delitem__() method."""
    del model[5]
    mock_remove.assert_called_with(5, 1)


def test_len(model):
    """Test the __len__() magic method."""
    assert len(model) == 10


def test_iter(model, model_objects):
    """Test the __iter__() method."""
    assert list(iter(model)) == model_objects


@mock.patch('cupi.ObjectModel.__getitem__')
def test_getObject(mock_get, model):
    """Test the getObject() convenience method."""
    model.getObject(5)
    mock_get.assert_called_with(5)


@mock.patch('cupi.ObjectModel.__setitem__')
def test_setObject(mock_set, model):
    """Test the setObject() convenience method."""
    new_obj = GenericObject()

    model.setObject(5, new_obj)

    mock_set.assert_called_with(5, new_obj)


@mock.patch('cupi.ObjectModel.beginRemoveRows')
@mock.patch('cupi.ObjectModel.endRemoveRows')
@mock.patch('cupi.ObjectModel._connect_to')
@mock.patch('cupi.ObjectModel._disconnect_from')
def test_removeRows(mock_disconnect, mock_connect, mock_end, mock_begin, model, model_objects):
    """Test the removeRows() method."""
    model.removeRows(5, 2)

    assert model.modified
    assert model.modifiedChanged.emit.called
    mock_begin.assert_called_with(mock.ANY, 5, 6)
    mock_disconnect.assert_called_with(model_objects[5])
    mock_disconnect.assert_called_with(model_objects[6])
    assert model_objects[5].parent() is None
    assert model_objects[6].parent() is None
    assert len(model) == 8


@mock.patch('cupi.ObjectModel.removeRows')
def test_removeRow(mock_remove, model):
    """Test the removeRow() method."""
    model.removeRow(5)
    mock_remove.assert_called_with(5, 1, mock.ANY)


@mock.patch('cupi.ObjectModel.__len__')
def test_length(mock_len, model):
    model.length()
    assert mock_len.called


@mock.patch('cupi.ObjectModel._connect_to')
def test_append(mock_connect, model):
    """Test the append() method."""
    new_obj = GenericObject()

    model.append(new_obj)

    assert model.modified
    assert model.modifiedChanged.emit.called
    assert len(model) == 11
    assert model[-1] is new_obj
    assert new_obj.parent() is model
    mock_connect.assert_called_with(new_obj)


@mock.patch('cupi.ObjectModel._connect_to')
@mock.patch('cupi.ObjectModel.beginInsertRows')
@mock.patch('cupi.ObjectModel.endInsertRows')
def test_insert(mock_end, mock_begin, mock_connect, model, model_objects):
    """Test the insert() method."""
    new_obj = GenericObject()

    model.insert(5, new_obj)

    mock_begin.assert_called_with(mock.ANY, 5, 5)
    assert len(model) == 11
    assert model[5] is new_obj
    assert model[6] is model_objects[5]
    mock_connect.assert_called_with(new_obj)
    assert new_obj.parent() is model
    assert mock_end.called


@mock.patch('cupi.ObjectModel._disconnect_from')
def test_apply(mock_disconnect, model_objects):
    """Test the apply() method."""
    first_objects = [GenericObject() for i in range(5)]
    for obj in itertools.chain(first_objects, model_objects):
        obj.apply = mock.Mock()

    # Create a model with an initial state, edit it, then call apply()
    model = qp.ObjectModel(GenericObject, first_objects)
    model.extend(model_objects)
    model.removeRows(0, len(first_objects))
    model.apply()

    # Objects that are being removed from the model should be disconnected and re-parented
    # They should not have their apply() method called
    for obj in first_objects:
        mock_disconnect.assert_called_with(obj)
        assert obj.parent() is None
        assert not obj.apply.called
        assert obj not in model

    # Objects that are staying in the model should stay connected, and have their apply() method called
    for obj in model_objects:
        assert obj in model
        assert obj not in mock_disconnect.call_args_list
        assert obj.apply.called

    assert len(model) == len(model_objects)
    assert not model.modified


@mock.patch('cupi.ObjectModel._connect_to')
@mock.patch('cupi.ObjectModel._disconnect_from')
def test_revert(mock_disconnect, mock_connect, model_objects):
    """Test the revert() method."""
    first_objects = [GenericObject() for i in range(5)]
    for obj in itertools.chain(first_objects, model_objects):
        obj.revert = mock.Mock()

    # Create a model with an initial state, edit it, then call revert()
    model = qp.ObjectModel(GenericObject, first_objects)
    model.extend(model_objects)
    model.removeRows(0, len(first_objects))
    model.revert()

    # Objects that are staying in the model should be re-connected, re-parented, and have their revert() method called
    for obj in first_objects:
        assert obj in model
        mock_connect.assert_called_with(obj)
        assert obj.parent() is model
        assert obj.revert.called

    # Objects that are being deleted from the model should be disconnected, re-parented, and NOT have their revert()
    # method called
    for obj in model_objects:
        assert obj not in model
        mock_disconnect.assert_called_with(obj)
        assert obj.parent() is None
        assert not obj.revert.called

    assert len(model) == len(first_objects)
    assert not model.modified


def test_index_and_parent(model):
    """Test the index() method."""
    assert not model.index(row=len(model) + 10, col=0).isValid()
    assert not model.index(row=0, col=model.columnCount() + 10).isValid()

    columns = len(qp.MapObjectMetaclass.properties[GenericObject.__name__])
    for row, col in itertools.product(range(len(model)), range(columns)):
        idx = model.index(row=row, col=col)
        assert idx.isValid()
        assert idx.row() == row
        assert idx.column() == col
        assert not model.parent(idx).isValid()


def test_rowCount(model, model_objects):
    """Test the rowCount() method."""
    assert model.rowCount() == len(model_objects)


def test_columnCount(model):
    """Test the columnCount() method."""
    columns = len(qp.MapObjectMetaclass.properties['GenericObject'])
    assert columns == model.columnCount()


def test_role(model):
    """Test the role() method."""
    for role, prop in enumerate(qp.MapObjectMetaclass.properties['GenericObject'], start=qtc.Qt.UserRole):
        assert model.role(prop) == role

    assert model.role('nonexistent property') == -1


def test_roleNames(model):
    """Test the roleNames() method."""
    role_names = model.roleNames()
    props = [prop.encode() for prop in qp.MapObjectMetaclass.properties['GenericObject']]
    roles = [role for role, prop in enumerate(props, start=qtc.Qt.UserRole)]

    assert list(role_names.keys()) == roles
    assert list(role_names.values()) == props


def test_columnNames(model):
    """Test the columnNames() method."""
    column_names = model.columnNames()
    assert column_names == qp.MapObjectMetaclass.properties['GenericObject']


def test_setColumns(model):
    """Test the setColumns() method."""
    column_names = list(reversed(model.columnNames()))
    model.setColumns(*column_names)
    assert model.columnNames() == column_names

    column_names = list(reversed(column_names))
    model.setColumns()
    assert model.columnNames() == column_names


def test_fieldIndex(model):
    """Test the fieldIndex() method."""
    for col, name in enumerate(model.columnNames()):
        assert model.fieldIndex(name) == col


def test_data(model, model_objects):
    """Test the data() method."""
    # Check the default behavior
    idx = qtc.QModelIndex()
    data = model.data(idx, 12345)
    assert isinstance(data, qtc.QVariant)
    assert not data.isValid()

    props = qp.MapObjectMetaclass.properties['GenericObject']

    for row, prop in enumerate(props):
        col = model.fieldIndex(prop)
        idx = model.index(row, col)
        role = model.role(prop)

        # Check using custom role values
        assert model.data(idx, role) == getattr(model_objects[row], prop)

        # Check using Qt.DisplayRole and the index's column value
        assert model.data(idx, qtc.Qt.DisplayRole) == getattr(model_objects[row], prop)


def test_connect_to(model):
    """Test the _connect_to() method."""
    # Check the default behavior
    model._connect_to(None)

    # Connect to a mock
    mock_object = mock.Mock(spec=GenericObject)
    model._connect_to(mock_object)

    for prop in qp.MapObjectMetaclass.properties['GenericObject']:
        signal_name = prop + 'Changed'
        getattr(mock_object, signal_name).connect.assert_called_with(model.onChildModified)


def test_disconnect_from(model):
    """Test the _disconnect_from() method."""
    # Check the default behavior
    model._disconnect_from(None)

    # Disconnect from a mock
    mock_object = mock.Mock(spec=GenericObject)
    model._disconnect_from(mock_object)

    for prop in qp.MapObjectMetaclass.properties['GenericObject']:
        signal_name = prop + 'Changed'
        getattr(mock_object, signal_name).disconnect.assert_called_with(model.onChildModified)


def test_onChildModified(model, model_objects):
    """Test the onChildModified signal handler."""
    model.dataChanged = mock.Mock()
    model_objects[5].genericProperty = 'cripes'

    # Check that dataChanged was emitted with the correct indices (once for genericProperty, once for modified)
    index1, index2 = model.dataChanged.emit.call_args_list[0][0]

    assert model.dataChanged.emit.call_count == 2
    assert index1.isValid()
    assert index2.isValid()
    assert index1.row() == 5
    assert index2.row() == 5
    assert index1.column() == 0
    assert index2.column() == model.columnCount() - 1
    assert model.modifiedChanged.emit.called


def test_document(model, model_objects):
    """Test the document property."""
    expected = [{'_type': 'GenericObject',
                 'generic_property': 'omg'} for obj in model_objects]

    doc = model.current_document
    assert doc == expected


def test_deleted(model, model_objects):
    """Test the deleted property."""
    model.removeRows(0, 5)
    deleted = model.deleted

    for row, obj in enumerate(deleted):
        assert obj is model_objects[row]

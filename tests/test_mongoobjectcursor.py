import pytest
import cupi as qp
import PyQt5.QtCore as qtc
import unittest.mock as mock


########################################################################################################################

TEST_COUNT = 5
TEST_CONTENTS = [{'key': 1},
                 {'key': 2},
                 {'key': 3},
                 {'key': 4},
                 {'key': 5}]

@pytest.fixture
def mock_cursor():
    m = mock.MagicMock()
    m.count.return_value = TEST_COUNT
    m.__iter__.return_value = TEST_CONTENTS
    return m


@pytest.fixture
def mock_database():
    return mock.Mock()


@pytest.fixture
def object_cursor(mock_cursor, mock_database):
    return qp.MongoObjectCursor(mock_cursor, database=mock_database)


########################################################################################################################


@pytest.mark.parametrize('database', [mock.MagicMock(), None])
@pytest.mark.parametrize('default_type', [qp.MapObject, None])
@pytest.mark.parametrize('parent', [qtc.QObject(), None])
def test_init(database, default_type, parent):
    """Test the MongoObjectCursor __init__ method."""
    # Build the keyword dictionary
    test_kwargs = {'database': database,
                   'default_type': default_type,
                   'parent': parent}
    test_kwargs = {k: v for k, v in test_kwargs.items() if v is not None}
    mock_cursor = mock.MagicMock()
    mock_cursor.count.return_value = 5

    curs = qp.MongoObjectCursor(mock_cursor, **test_kwargs)

    mock_cursor.count.assert_called_once()
    assert curs.count == TEST_COUNT
    mock_cursor.__iter__.assert_called_once()


def test_del(mock_cursor, mock_database):
    """Test the __del__ method."""
    m = qp.MongoObjectCursor(mock_cursor, mock_database)
    del m

    mock_cursor.close.assert_called_once()


@mock.patch('cupi.mongodatabase.MongoDatabase.unescaped')
@mock.patch('cupi.objects.MapObject.from_document')
def test_dunder_next(mock_from_doc, mock_unescaped, object_cursor):
    """Test the __next__ method."""
    object_cursor.doneChanged = mock.MagicMock()

    for idx, expected in enumerate(TEST_CONTENTS):
        result = next(object_cursor)
        mock_unescaped.assert_called_with(expected)
        mock_from_doc.assert_called_with(mock_unescaped.return_value, default_type=mock.ANY)
        assert result is mock_from_doc.return_value

    with pytest.raises(StopIteration):
        next(object_cursor)

    assert object_cursor.done
    object_cursor.doneChanged.emit.assert_called_once()

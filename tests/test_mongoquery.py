import pytest
import unittest.mock as mock
import cupi as qp
import PyQt5.QtCore as qtc
import pymongo

########################################################################################################################


@pytest.fixture
def query():
    return qp.MongoQuery()


INVALID_ROLE = 'some arbitrary value'
@pytest.fixture(params=[12345, '12345', '$#%$@', None, INVALID_ROLE])
def role(request):
    return request.param


@pytest.fixture(params=[12345, 123.45, '12345', '$%^$#!@.', None])
def value(request):
    return request.param

FILTER_TYPES = ['value', 'regex', 'range_min', 'range_max']
@pytest.fixture(params=FILTER_TYPES + ['INVALID'])
def filter_type(request):
    return request.param


########################################################################################################################


@pytest.mark.parametrize('test_doc', [{}, [], {'sub': {}}, {'sub': []}])
def test_clean(test_doc):
    """The the _clean() method."""
    doc = {'permanent_key': 'stay!',
           'test_key': test_doc}

    qp.MongoQuery._clean(doc)

    assert len(doc) == 1
    assert 'permanent_key' in doc
    assert 'test_key' not in doc


def test_filterBy(query, role, filter_type, value):
    """Test the filterBy() method."""
    if role is None or filter_type not in FILTER_TYPES:
        with pytest.raises(ValueError):
            query.filterBy(role, filter_type, value)
        return

    query.filterBy(role, filter_type, value)

    if filter_type == 'value':
        assert query.query[role] == value
    elif filter_type == 'regex':
        assert query.query[role] == {'$regex': value, '$options': 'i'}
    elif filter_type == 'range_min':
        assert query.query[role]['$gte'] == value
    elif filter_type == 'range_max':
        assert query.query[role]['$lte'] == value


def test_getFilter(query, role, filter_type, value):
    """Test the getFilter() method."""
    if role is None or filter_type not in FILTER_TYPES:
        with pytest.raises(ValueError):
             query.getFilter(role, filter_type)
        return

    # Check that calling getFilter on an unset filter returns None
    assert query.getFilter(role, filter_type) is None

    # Set filter and then check using getFilter
    query.filterBy(role, filter_type, value)
    assert query.getFilter(role, filter_type) == value


def test_deleteFilter(query, role, filter_type, value):
    """Test the deleteFilter() method."""
    if role is None:
        with pytest.raises(ValueError):
            query.deleteFilter(role)
    elif filter_type not in FILTER_TYPES:
        query.deleteFilter(role)
    else:
        query.filterBy(role, filter_type, value)
        query.deleteFilter(role)

        assert role not in query.query

@pytest.mark.parametrize('order', [qtc.Qt.AscendingOrder, qtc.Qt.DescendingOrder, 5, -5])
def test_sortBy(query, role, order):
    """Test the sortBy() method."""
    if order not in [qtc.Qt.AscendingOrder, qtc.Qt.DescendingOrder]:
        with pytest.raises(ValueError):
            query.sortBy(role, order)
    else:
        query.sortBy(role, order)

        if order == qtc.Qt.AscendingOrder:
            assert query.sort[role] == pymongo.ASCENDING
        elif order == qtc.Qt.DescendingOrder:
            assert query.sort[role] == pymongo.DESCENDING

@pytest.mark.parametrize('order', [qtc.Qt.AscendingOrder, qtc.Qt.DescendingOrder])
def test_getSortOrder(query, role, order):
    """Test the getSortOrder() method."""
    if role is None:
        with pytest.raises(ValueError):
            query.getSortOrder(role)
    elif role is INVALID_ROLE:
        assert query.getSortOrder(role) is None
    else:
        query.sortBy(role, order)
        assert query.getSortOrder(role) == order
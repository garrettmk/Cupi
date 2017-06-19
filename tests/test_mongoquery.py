import pytest
import unittest.mock as mock
import cupi as qp

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


########################################################################################################################


def test_filterByValue(query, role, value):
    """Test the filterByValue() method."""
    if role is None:
        with pytest.raises(ValueError):
            query.filterByValue(role, value)
    else:
        query.filterByValue(role, value)
        assert query.query[role] == value


def test_getFilterValue(query, role, value):
    """Test the getFilterValue() method."""
    if role is None:
        with pytest.raises(ValueError):
            query.getFilterValue(role)

    elif role == INVALID_ROLE:
        assert query.getFilterValue(role) is None

    else:
        query.filterByValue(role, value)
        assert query.getFilterValue(role) == value


def test_filterByRegex(query, role, value):
    """Test the filterByRegex() method."""
    if role is None:
        with pytest.raises(ValueError):
            query.filterByRegex(role, value)
    elif value is None:
        query.filterByRegex(role, 'some regex')
        query.filterByRegex(role, None)
        with pytest.raises(KeyError):
            query.query[role]
    else:
        query.filterByRegex(role, value)
        assert query.query[role]['$regex'] == value


def test_getFilterRegex(query, role, value):
    """Test the getFilterRegex() method."""
    if role is None:
        with pytest.raises(ValueError):
            query.getFilterRegex(role)
    elif role == INVALID_ROLE:
        assert query.getFilterRegex(role) is None
    else:
        query.filterByRegex(role, value)
        assert query.getFilterRegex(role) == value


def test_setFilterRangeMin(query, role, value):
    """Test the setFilterRangeMin() method."""
    if role is None:
        with pytest.raises(ValueError):
            query.setFilterRangeMin(role, value)
    elif value is None:
        query.setFilterRangeMin(role, 'some value')
        query.setFilterRangeMin(role, None)
        with pytest.raises(KeyError):
            query.query[role]['$gte']
    else:
        query.setFilterRangeMin(role, value)
        assert query.query[role]['$gte']

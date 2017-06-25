import pytest
import cupi as qp
import PyQt5.QtCore as qtc
import unittest.mock as mock


########################################################################################################################


class GenericObject(qp.MapObject):
    testProperty = qp.Property('test_property', int)


TEST_COUNT = 25
TEST_PAGE_SIZE = 10
TEST_CONTENTS = [GenericObject({'test_property': i}) for i in range(TEST_COUNT)]


########################################################################################################################


@mock.patch('cupi.CursorObjectModel.endInsertRows')
@mock.patch('cupi.CursorObjectModel.beginInsertRows')
def test_fetchMore(mock_begin_insert, mock_end_insert):
    """Test the fetchMore() method."""
    # Create a mock cursor
    mock_cursor = mock.MagicMock()
    mock_cursor.count = TEST_COUNT
    mock_cursor.__next__.side_effect = TEST_CONTENTS

    # Create a test object
    curs = qp.CursorObjectModel(GenericObject, mock_cursor, page_size=TEST_PAGE_SIZE)

    # Check that the first page was loaded
    assert len(curs) == TEST_PAGE_SIZE
    assert not curs.modified
    mock_begin_insert.assert_called_with(mock.ANY, 0, TEST_PAGE_SIZE - 1)
    mock_end_insert.assert_called_once()

    # Load the next pages
    full_pages = len(TEST_CONTENTS) // TEST_PAGE_SIZE

    for page_num in range(1, full_pages):
        mock_begin_insert.reset_mock()
        mock_end_insert.reset_mock()

        curs.fetchMore()

        assert len(curs) == (page_num + 1) * TEST_PAGE_SIZE
        assert not curs.modified
        mock_begin_insert.assert_called_with(mock.ANY, TEST_PAGE_SIZE, (page_num + 1) * TEST_PAGE_SIZE - 1)
        mock_end_insert.assert_called_once()

    # Check for and load the fractional page at the end
    last_page_len = len(TEST_CONTENTS) % TEST_PAGE_SIZE

    if last_page_len > 0:
        mock_begin_insert.reset_mock()
        mock_end_insert.reset_mock()

        curs.fetchMore()

        assert len(curs) == len(TEST_CONTENTS)
        assert not curs.modified
        mock_begin_insert.assert_called_with(mock.ANY, TEST_PAGE_SIZE * full_pages, len(TEST_CONTENTS) - 1)
        mock_end_insert.assert_called_once()

    # Calling this now should do nothing
    curs.fetchMore()


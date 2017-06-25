import pytest
import cupi as qp
import unittest.mock as mock


########################################################################################################################


UNESCAPED_DOC = {'$one': '$one',
                 '$one.two': ['$one', '$two'],
                 '$one.two.three': {'$one': 1,
                                    '$two': 2,
                                    '$three': 3}}

ESCAPED_DOC = {'＄one': '$one',
               '＄one．two': ['$one', '$two'],
               '＄one．two．three': {'＄one': 1,
                                    '＄two': 2,
                                    '＄three': 3}}


########################################################################################################################


def test_escaped():
    """Test the escaped() method."""
    assert qp.MongoDatabase.escaped(UNESCAPED_DOC) == ESCAPED_DOC
    assert qp.MongoDatabase.unescaped(ESCAPED_DOC) == UNESCAPED_DOC

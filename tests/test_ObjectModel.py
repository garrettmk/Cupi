import pytest
import cupi as qp
import PyQt5.QtCore as qtc
import PyQt5.QtQml as qtq
import unittest.mock as mock


########################################################################################################################


class GenericObject(qp.MapObject):

    genericPropertyChanged = qtc.pyqtSignal()
    genericProperty = qp.Property(str, 'generic_property', notify=genericPropertyChanged)


########################################################################################################################


@pytest.fixture(params=[True, False])
def generic_parent(request):
    if request.param is True:
        return qtc.QObject()
    else:
        return None


@pytest.fixture(params=[True, False])
def generic_objects(request):
    if request.param is True:
        return [GenericObject(genericProperty='omg') for i in range(10)]
    else:
        return None


########################################################################################################################


@pytest.mark.parametrize('_type', [GenericObject, 'GenericObject', qp.MapObjectReference])
@pytest.mark.parametrize('ref_type', [GenericObject, 'GenericObject', None])
@pytest.mark.parametrize('listen', [False, True])
def test_init(_type, ref_type, generic_objects, listen, generic_parent):
    """Test the ObjectModel __init__ method."""
    model = qp.ObjectModel(_type=_type, ref_type=ref_type, objects=generic_objects, listen=listen, parent=generic_parent)

    # Check that the parent is set correctly
    assert qtc.QObject.parent(model) is generic_parent

    #
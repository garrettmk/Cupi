import pytest
import cupi as qp
import PyQt5.QtCore as qtc
import unittest.mock as mock


########################################################################################################################


@pytest.fixture(scope='session')
def app():
    return qp.App([])


class ClassA:
    pass


class ClassB(ClassA):
    pass


class ClassC(ClassA):
    pass


class ClassD(ClassC):
    pass


class ClassE(ClassC, ClassB):
    pass


ALL_SUBCLASSES = [ClassA, ClassB, ClassC, ClassD, ClassE]


########################################################################################################################


@pytest.mark.parametrize("version_major", [None, 12345])
@pytest.mark.parametrize('version_minor', [None, 45678])
@pytest.mark.parametrize('qml_uri', [None, 'qml uri value'])
@mock.patch('PyQt5.QtQml.qmlRegisterType')
def test_register_class_single(mock_register, app, qml_uri, version_major, version_minor):
    """Test the register_class() method."""
    # Build the mock class
    mock_attribs = {'__qml_uri__': qml_uri,
                    '__version_major__': version_major,
                    '__version_minor__': version_minor,
                    '__name__': 'class name'}
    mock_attribs = {k: v for k, v in mock_attribs.items() if v is not None}
    mock_class = mock.MagicMock(**mock_attribs)

    # Build the expected call arguments
    expected_args = [mock_class,
                     mock_class.__qml_uri__ if qml_uri else mock_class.__name__,
                     mock_class.__version_major__ if version_major else 1,
                     mock_class.__version_minor__ if version_minor else 0,
                     mock_class.__name__]

    # Do the test call
    app.register_class(mock_class)

    # Check
    assert mock_register.call_args == mock.call(*expected_args)


@mock.patch('PyQt5.QtQml.qmlRegisterType')
def test_register_subclasses_descendants(mock_register, app):
    """Test the register_subclasses() method."""
    app.register_class(ClassA, descendants=True)
    assert len(mock_register.call_args_list) == len(ALL_SUBCLASSES)
    for cls in ALL_SUBCLASSES:
        assert mock.call(cls, mock.ANY, mock.ANY, mock.ANY, mock.ANY) in mock_register.call_args_list


@pytest.mark.parametrize('load_file', [None, 'test file'])
@pytest.mark.parametrize('auto_register', [None, True, False])
@pytest.mark.parametrize('cupi_path', [None, 'test path'])
@pytest.mark.parametrize('app_name', [None, 'App Name'])
@pytest.mark.parametrize('org', [None, 'Test Company'])
@mock.patch('cupi.application.App.prepare_root_context')
@mock.patch('cupi.application.App.register_class')
@mock.patch('PyQt5.QtQml.QQmlApplicationEngine')
@mock.patch('cupi.application.App.setApplicationName')
@mock.patch('cupi.application.App.setOrganizationName')
def test_prepare(mock_setorgname, mock_setappname, mock_qmlengine_factory, mock_register, mock_prepcontext,
                 app, org, app_name, cupi_path, auto_register, load_file):
    """Test the prepare() method."""
    # Build the test kwargs
    test_kwargs = {'organization': org,
                   'application': app_name,
                   'cupi_path': cupi_path,
                   'auto_register': auto_register,
                   'load_file': load_file}
    test_kwargs = {k: v for k, v in test_kwargs.items() if v is not None}

    # Do the test call
    app.prepare(**test_kwargs)
    mock_qmlengine = mock_qmlengine_factory.return_value

    # If an organization name was provided, then it should be used to call
    # to QApplication.setOrganizationName()
    if org is not None:
        mock_setorgname.assert_called_with(org)
    else:
        mock_setorgname.assert_not_called()

    # If an application name was provided, then it should be used to call
    # to QApplication.setApplicationName()
    if app_name is not None:
        mock_setappname.assert_called_with(app_name)
    else:
        mock_setappname.assert_not_called()

    # Check that a QML engine was created
    mock_qmlengine_factory.assert_called_with(app)

    # If a path to the Cupi engine was provided, use it as an import path
    # for the QML engine
    if cupi_path is not None:
        mock_qmlengine.addImportPath.assert_called_with(cupi_path)

    # If MapObject, ObjectModel, and MongoDatabase (and their subclasses) should
    # be registered by default.
    if auto_register is True or auto_register is None:
        for cls in [qp.MapObject, qp.ObjectModel, qp.MongoDatabase]:
            assert mock.call(cls, descendants=True) in mock_register.call_args_list
    else:
        mock_register.assert_not_called()

    # The prepare_root_context() method should be called with the QML engine's
    # root context as a parameter
    mock_prepcontext.assert_called_with(mock_qmlengine.rootContext.return_value)

    # If a QML file path was provided, load the file
    if load_file is not None:
        mock_qmlengine.load.assert_called_with(load_file)
    else:
        mock_qmlengine.load.assert_not_called()
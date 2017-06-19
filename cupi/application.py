import PyQt5.QtWidgets as qtw

from .mongodatabase import *
from .objects import *


class App(qtw.QApplication):
    """An Application class that provides a few convenience services."""

    def __init__(self, *args, **kwargs):
        """Initialize the application."""
        super().__init__(*args, **kwargs)
        self._qml_engine = None

    @property
    def engine(self):
        return self._qml_engine

    def register_class(self, cls, descendants=False, _already_registered=None):
        """Registers a class with the QML engine."""
        _already_registered = [] if _already_registered is None else _already_registered

        version_major = getattr(cls, '__version_major__', 1)
        version_minor = getattr(cls, '__version_minor__', 0)
        uri = getattr(cls, '__qml_uri__', cls.__name__)

        qtq.qmlRegisterType(cls, uri, version_major, version_minor, cls.__name__)
        _already_registered.append(cls)

        if descendants:
            for subcls in cls.__subclasses__():
                if subcls not in _already_registered:
                    self.register_class(subcls, descendants=True, _already_registered=_already_registered)

    def prepare(self, load_file=None, organization=None, application=None, cupi_path=None, auto_register=True):
        """Prepare the application to run."""
        # Set the application and organization names
        if organization is not None:
            self.setOrganizationName(organization)

        if application is not None:
            self.setApplicationName(application)

        # Create the QML engine
        self._qml_engine = qtq.QQmlApplicationEngine(self)

        # Add the Cupi import path
        if cupi_path is not None:
            self._qml_engine.addImportPath(cupi_path)

        # Register subtypes
        if auto_register:
            for cls in [MapObject, ObjectModel, MongoDatabase]:
                self.register_class(cls, descendants=True)

        # Prepare the root context
        context = self._qml_engine.rootContext()
        self.prepare_root_context(context)

        # Load the main QML file
        if load_file is not None:
            self._qml_engine.load(load_file)

    def prepare_root_context(self, context):
        """Prepare the root context before loading the main QML file. Provided by subclasses."""

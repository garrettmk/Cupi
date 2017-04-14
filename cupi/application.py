import sys
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtQml as qtq

from .mongodatabase import *
from .objects import *
from .objectmodel import *


class App(qtg.QGuiApplication):
    """An Application class that provides a few convenience services."""

    def __init__(self, *args, qml='main.qml', **kwargs):
        """Initialize the application.

        Arguments:      qml                 The path to the main QML file
                        organization        The name of the organization.
                        app_name            The name of the application.
        """
        super().__init__(*args, **kwargs)

        self._qml_engine = None

    @property
    def engine(self):
        return self._qml_engine

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
            self.register_subclasses(DocumentObject, MongoDatabase)

        # Prepare the root context
        context = self._qml_engine.rootContext()
        self.prepare_root_context(context)

        # Load the main QML file
        if load_file is not None:
            self._qml_engine.load(load_file)

    @staticmethod
    def _all_subclasses(cls):
        """Return a list of all the subclasses of cls."""
        return cls.__subclasses__() + [desc for base in cls.__subclasses__() for desc in App._all_subclasses(base)]

    def register_subclasses(self, *args):
        """Registers all subclasses of cls with the QML engine."""
        for cls in args:
            for sub in App._all_subclasses(cls):
                version_major = getattr(sub, '__version_major__', 1)
                version_minor = getattr(sub, '__version_minor__', 0)
                uri = getattr(sub, '__qml_uri__', sub.__name__)

                qtq.qmlRegisterType(sub, uri, version_major, version_minor, sub.__name__)

    def prepare_root_context(self, context):
        """Prepare the root context before loading the main QML file. Provided by subclasses."""

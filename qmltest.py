import sys
import cupi as qp

from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.QtWidgets import QApplication


if __name__ == '__main__':
    # Create the application
    app = QApplication(sys.argv)

    # Create the QML Engine
    engine = QQmlApplicationEngine(app)
    engine.addImportPath('.')

    # Register types
    qp.MapObject.register_subclasses()

    # Load the QML file
    engine.load('qmltest.qml')

    # Go
    app.exec_()
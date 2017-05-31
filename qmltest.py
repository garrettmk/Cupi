import sys
import cupi as qp

import PyQt5.QtCore as qtc


########################################################################################################################


class TestObject(qp.MapObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._list = qp.ListObject(['One', 'Two', 'Three'])

    listPropChanged = qtc.pyqtSignal()
    @qtc.pyqtProperty(qtc.QVariant, notify=listPropChanged)
    def listProp(self):
        return self._list

    @listProp.setter
    def listProp(self, value):
        self._list = value


########################################################################################################################


class TestApp(qp.App):
    def __init__(self, *args):
        super().__init__(*args)
        self._test_object = TestObject()

    def prepare_root_context(self, context):
        context.setContextProperty('test_object', self._test_object)


########################################################################################################################


if __name__ == '__main__':
    # Create the application
    app = TestApp(sys.argv)
    app.prepare(load_file='qmltest.qml',
                application='CupiQMLTest',
                cupi_path='.')
    # Go
    app.exec_()
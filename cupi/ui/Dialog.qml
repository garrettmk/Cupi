import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import "." as QP

Window {
    id: root
    flags: Qt.Window
    color: QP.Theme.backgroundColor
    width: contentItem.children.length === 1 ? contentItem.children[0].implicitWidth : contentItem.childrenRect.width
    height: contentItem.children.length === 1 ? contentItem.children[0].implicitHeight : contentItem.childrenRect.height

    // Properties
    default property alias panelContent: panel.data
    property alias title: panel.title

    // Signals
    signal accepted()
    signal rejected()

    // Methods
    function accept() {
        accepted()
        close()
    }

    function reject() {
        rejected()
        close()
    }

    Component.onCompleted: {
        width = width
        height = height
        minimumWidth = width
        minimumHeight = height
    }

    // Body
    QP.Panel {
        id: panel
        folds: false
        border.width: QP.Theme.borderWidthBig
        anchors.fill: parent
        titlePointSize: QP.Theme.textPointSizeBig

        // Dialog content goes here

    }
}

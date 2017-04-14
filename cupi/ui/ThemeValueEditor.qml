import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import "." as QP

QP.Panel {
    id: root
    property alias themeValues: repeater.model
    property real minimumValue: 0
    property real maximumValue: 5000

    default property alias displayDelegate: delegate.children

    ColumnLayout {
        anchors.centerIn: parent

        Repeater {
            id: repeater

            RowLayout {

                QP.Text {
                    text: modelData + ":"
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 150
                }

                QP.SpinBox {
                    value: QP.Theme[modelData]
                    minimumValue: root.minimumValue
                    maximumValue: root.maximumValue
                    onValueChanged: QP.Theme[modelData] = value
                }

                Item {
                    id: delegate
                    Layout.preferredWidth: delegate.children.length === 1 ? delegate.children[0].implicitWidth : delegate.childrenRect.width
                    Layout.preferredHeight: delegate.children.length === 1 ? delegate.children[0].implicitHeight : delegate.childrenRect.height
                }
            }

        }

    }
}

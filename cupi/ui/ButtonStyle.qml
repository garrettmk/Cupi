import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as QP

ButtonStyle {
    id: root

    property real borderAlpha: control.hovered || control.activeFocus ? 1 : 0.5
    Behavior on borderAlpha {NumberAnimation {duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}}
    property int fontPointSize: QP.Theme.textPointSize
    property bool fontBold: false
    property int defaultWidth: 100
    property int defaultHeight: 25
    property int radius: QP.Theme.radiusMid

    background: Rectangle {
        id: bg
        color: "transparent"
        radius: root.radius
        border.color: Qt.rgba(QP.Theme.borderColor.r, QP.Theme.borderColor.g, QP.Theme.borderColor.b, borderAlpha)
        border.width: QP.Theme.borderWidthSmall
        implicitWidth: backgroundImage.status === Image.Ready ? backgroundImage.implicitWidth : root.defaultWidth
        implicitHeight: backgroundImage.status === Image.Ready ? backgroundImage.implicitHeight : root.defaultHeight

        Connections {
            target: control
            onPressedChanged: {
                if (control.pressed) {
                    toReleased.stop()
                    toPressed.start()
                } else {
                    toPressed.stop()
                    toReleased.start()
                }
            }
        }

        ColorAnimation on color {
            id: toPressed
            from: "transparent"
            to: QP.Theme.highlightColor
            duration: QP.Theme.durationShort
            running: false
            alwaysRunToEnd: true
        }

        ColorAnimation on color {
            id: toReleased
            from: QP.Theme.highlightColor
            to: "transparent"
            duration: QP.Theme.durationShort
            running: false
            alwaysRunToEnd: true
        }

        Image {
            id: backgroundImage
            anchors {
                fill: parent
                margins: parent.border.width + 2
            }
            fillMode: Image.PreserveAspectFit
            source: control.iconSource
        }
    }

    label: QP.Text {
        id: label
        text: control.text
        opacity: control.enabled ? 1 : 0.5
        anchors.fill: parent
        font.bold: root.fontBold
        font.pointSize: root.fontPointSize
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter

        Behavior on opacity {NumberAnimation {duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}}
    }
}

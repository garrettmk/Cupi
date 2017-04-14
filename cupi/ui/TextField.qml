import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as QP

TextField {

    // Properties
    property bool backgroundVisible: true

    style: TextFieldStyle {
        property real borderAlpha: control.hovered || control.activeFocus ? 1 : 0.5
        Behavior on borderAlpha {NumberAnimation {duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}}

        background: Rectangle {
            visible: backgroundVisible
            color: "transparent"

            Rectangle {
                radius: QP.Theme.radiusSmall
                color: Qt.rgba(QP.Theme.borderColor.r, QP.Theme.borderColor.g, QP.Theme.borderColor.b, borderAlpha)
                height: QP.Theme.borderWidthSmall
                width: parent.width
                anchors.bottom: parent.bottom
            }
        }

        textColor: QP.Theme.textColor
        selectionColor: QP.Theme.textSelectionColor
        selectedTextColor: QP.Theme.selectedTextColor
        placeholderTextColor: Qt.rgba(QP.Theme.textColor.r, QP.Theme.textColor.g, QP.Theme.textColor.b, 0.25)
    }
}

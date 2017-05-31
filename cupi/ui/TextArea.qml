import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as QP

TextArea {
    style: TextAreaStyle {
        backgroundColor: "transparent"
        textColor: QP.Theme.textColor
        selectionColor: QP.Theme.textSelectionColor
        selectedTextColor: QP.Theme.selectedTextColor
        font.pointSize: QP.Theme.textPointSize
        textMargin: QP.Theme.spacingMid
        renderType: Text.QtRendering

        property real borderAlpha: control.activeFocus ? 1 : 0.5
        Behavior on borderAlpha {NumberAnimation {duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}}

        frame: Rectangle {
            color: "transparent"
            radius: QP.Theme.radiusSmall
            border.width: QP.Theme.borderWidthSmall
            border.color: Qt.rgba(QP.Theme.borderColor.r, QP.Theme.borderColor.g, QP.Theme.borderColor.b, borderAlpha)
        }

        decrementControl: Item {width: styleData.horizontal ? 1 : 0; height: styleData.horizontal ? 0 : 1}
        incrementControl: Item {width: styleData.horizontal ? 2 : 0; height: styleData.horizontal ? 0 : 2}
        scrollBarBackground: Rectangle {
            color: "transparent"
            implicitWidth: styleData.horizontal ? 50 : 9
            implicitHeight: styleData.horizontal ? 9 : 50
        }

        handle: Rectangle {
            color: QP.Theme.borderColor
            implicitWidth: styleData.horizontal ? 50 : 8
            implicitHeight: styleData.horizontal ? 8 : 50
            radius: 4
            opacity: 0.75
        }

        transientScrollBars: true
    }

    backgroundVisible: false
}

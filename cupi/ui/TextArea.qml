import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

TextArea {
    style: TextAreaStyle {
        backgroundColor: "transparent"
        textColor: Themed.Theme.textColor
        selectionColor: Themed.Theme.textSelectionColor
        selectedTextColor: Themed.Theme.selectedTextColor
        font.pointSize: Themed.Theme.textPointSize
        textMargin: Themed.Theme.spacingMid

        property real borderAlpha: control.activeFocus ? 1 : 0.5
        Behavior on borderAlpha {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}

        frame: Rectangle {
            color: "transparent"
            radius: Themed.Theme.radiusSmall
            border.width: Themed.Theme.borderWidthSmall
            border.color: Qt.rgba(Themed.Theme.borderColor.r, Themed.Theme.borderColor.g, Themed.Theme.borderColor.b, borderAlpha)
        }

        decrementControl: Item {height: 1}
        incrementControl: Item {height: 2}
        scrollBarBackground: Rectangle {
            color: "transparent"
            implicitWidth: 9
            implicitHeight: 50
        }

        handle: Rectangle {
            color: Themed.Theme.borderColor
            implicitWidth: 8
            implicitHeight: 50
            radius: 4
            opacity: 0.75
        }

        transientScrollBars: true
    }

    backgroundVisible: false
}

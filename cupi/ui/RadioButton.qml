import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

RadioButton {
    style: RadioButtonStyle {
        indicator: Rectangle {
            implicitWidth: labelMetrics.font.pixelSize
            implicitHeight: labelMetrics.font.pixelSize
            anchors.bottomMargin: 5
            radius: implicitWidth / 2
            color: "transparent"
            border.width: Themed.Theme.borderWidthSmall
            border.color: Themed.Theme.borderWithAlpha(borderAlpha)

            property real borderAlpha: control.hovered || control.activeFocus ? 1 : 0.5
            Behavior on borderAlpha {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}

            TextMetrics {
                id: labelMetrics
                text: control.text
                font.pointSize: Themed.Theme.textPointSize
            }

            Rectangle {
                color: Themed.Theme.highlightColor
                radius: (parent.height - 2 * parent.border.width) / 2
                anchors.fill: parent
                anchors.margins: 2
                opacity: control.checked ? 1 : 0
                Behavior on opacity {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}
            }

        }

        label: Themed.Text {id: label; text: control.text}
    }
}

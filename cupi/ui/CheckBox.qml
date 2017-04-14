import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as QP

CheckBox {
    style: CheckBoxStyle {
        indicator: Rectangle {
            implicitWidth: labelMetrics.font.pixelSize + 2
            implicitHeight: labelMetrics.font.pixelSize + 2
            radius: QP.Theme.radiusSmall
            color: "transparent"
            border.width: QP.Theme.borderWidthSmall
            border.color: QP.Theme.borderWithAlpha(borderAlpha)

            property real borderAlpha: control.hovered || control.activeFocus ? 1 : 0.5
            Behavior on borderAlpha {NumberAnimation {duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}}

            TextMetrics {
                id: labelMetrics
                text: control.text
                font.pointSize: QP.Theme.textPointSize
            }

            Rectangle {
                opacity: control.checked ? 1 : 0
                color: QP.Theme.highlightColor
                radius: QP.Theme.radiusSmall
                anchors.margins: 2
                anchors.fill: parent
                Behavior on opacity {NumberAnimation {duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}}

                // Check mark
                Canvas {
                    anchors.fill: parent
                    anchors.margins: 1
                    onPaint: {
                        var ctx = getContext("2d")

                        ctx.lineWidth = 2
                        ctx.strokeStyle = QP.Theme.backgroundColor

                        ctx.beginPath()
                        ctx.moveTo(0, height / 2)
                        ctx.lineTo(width / 2, height)
                        ctx.lineTo(width, 0)

                        ctx.stroke()
                    }
                }
            }
        }

        label: QP.Text {text: control.text}
    }
}

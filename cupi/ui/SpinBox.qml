import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

SpinBox {
    style: SpinBoxStyle {
        id: style
        textColor: Themed.Theme.textColor
        selectionColor: Themed.Theme.highlightColor
        selectedTextColor: Themed.Theme.selectedTextColor
        font.pointSize: Themed.Theme.textPointSize
        horizontalAlignment: Qt.AlignRight

        property real borderAlpha: control.hovered || control.activeFocus ? 1 : 0.5
        Behavior on borderAlpha {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}

        background: Rectangle {
            color: "transparent"
            implicitWidth: 80
            implicitHeight: 20

            Rectangle {
                width: parent.width
                height: Themed.Theme.borderWidthSmall
                anchors.bottom: parent.bottom
                color: Qt.rgba(Themed.Theme.borderColor.r, Themed.Theme.borderColor.g, Themed.Theme.borderColor.b, borderAlpha)
                radius: Themed.Theme.radiusSmall
            }
        }

        incrementControl: Item {
            implicitWidth: 10
            visible: control.enabled

            Item {
                clip: true
                anchors.fill: parent
                anchors.bottomMargin: 1

                Rectangle {
                    rotation: 45
                    color: Qt.rgba(Themed.Theme.borderColor.r, Themed.Theme.borderColor.g, Themed.Theme.borderColor.b, borderAlpha)
                    width: Math.round(parent.width / Math.sqrt(2))
                    height: width
                    anchors {
                        horizontalCenter: parent.horizontalCenter
                        verticalCenter: parent.bottom
                    }
                }
            }
        }

        decrementControl: Item {
            implicitWidth: 10
            visible: control.enabled

            Item {
                clip: true
                anchors.fill: parent
                anchors.topMargin: 2

                Rectangle {
                    rotation: 45
                    color: Qt.rgba(Themed.Theme.borderColor.r, Themed.Theme.borderColor.g, Themed.Theme.borderColor.b, borderAlpha)
                    width: Math.round(parent.width / Math.sqrt(2))
                    height: width
                    anchors {
                        horizontalCenter: parent.horizontalCenter
                        verticalCenter: parent.top
                        verticalCenterOffset: 1
                    }
                }
            }
        }


    }
}

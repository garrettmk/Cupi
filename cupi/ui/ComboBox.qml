import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

ComboBox {
    style: ComboBoxStyle {
        id: style

        property real borderAlpha: control.hovered || control.activeFocus ? 1 : 0.5
        Behavior on borderAlpha {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}

        label: Themed.Text {
            text: control.currentText
            font.bold: true
            clip: true
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            anchors.fill: parent
        }

        background: Item {
            implicitWidth: 125

            // Underline
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                color: Themed.Theme.borderColor
                opacity: borderAlpha
                height: Themed.Theme.borderWidthSmall
                radius: Themed.Theme.radiusSmall
            }

            // Side button
            Item {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 10

                Item {
                    clip: true
                    width: parent.width
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.verticalCenter
                    anchors.bottomMargin: 1

                    Rectangle {
                        rotation: 45
                        color: Themed.Theme.borderColor
                        opacity: borderAlpha
                        width: Math.round(parent.width / Math.sqrt(2))
                        height: width
                        anchors {
                            horizontalCenter: parent.horizontalCenter
                            verticalCenter: parent.bottom
                        }
                    }
                }

                Item {
                    clip: true
                    width: parent.width
                    anchors.top: parent.verticalCenter
                    anchors.topMargin: 1
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom

                    Rectangle {
                        rotation: 45
                        color: Themed.Theme.borderColor
                        opacity: borderAlpha
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
}

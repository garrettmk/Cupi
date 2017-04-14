import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

StatusBar {
    style: StatusBarStyle {
        padding {
            left: Themed.Theme.spacingMid
            right: Themed.Theme.spacingMid
            top: Themed.Theme.spacingSmall
            bottom: Themed.Theme.spacingSmall
        }

        background: Rectangle {
            color: Themed.Theme.backgroundColorMid

            Rectangle {
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                }
                height: Themed.Theme.borderWidthMid
                color: Themed.Theme.borderColorDark
            }
        }
    }
}

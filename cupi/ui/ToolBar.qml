import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

ToolBar {
    style: ToolBarStyle {
        padding {
            top: Themed.Theme.spacingSmall + Math.round(Themed.Theme.radiusMid / 2)
            left: Themed.Theme.spacingMid
            right: Themed.Theme.spacingMid
            bottom: Themed.Theme.spacingSmall + Themed.Theme.radiusMid
        }

        background: Rectangle {
            color: Themed.Theme.backgroundColorMid
            Rectangle {
                anchors {
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                }
                height: Themed.Theme.borderWidthMid
                color: Themed.Theme.borderColorDark
            }
        }
    }
}

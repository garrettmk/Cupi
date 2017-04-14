import QtQuick 2.7
import "." as Themed

Rectangle {
    id: background
    width: contentsRow.childrenRect.width + 2 * Themed.Theme.spacingSmall
    height: tagText.height + 2 * (Themed.Theme.spacingSmall - 2)
    color: Qt.rgba(Themed.Theme.backgroundColorLight.r, Themed.Theme.backgroundColorLight.g, Themed.Theme.backgroundColorLight.b, borderAlpha)
    radius: Themed.Theme.radiusSmall

    property real borderAlpha: mouseArea.containsMouse ? 1 : 0.5
    Behavior on borderAlpha {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}

    property alias text: tagText.text

    signal tagClicked(string tag)
    signal tagClosed(string tag)

    ColorAnimation on color {
        id: toPressed
        from: Themed.Theme.backgroundColorLight
        to: Themed.Theme.highlightColor
        duration: Themed.Theme.durationShort
        alwaysRunToEnd: true
        running: false
    }

    ColorAnimation on color {
        id: toReleased
        from: Themed.Theme.highlightColor
        to: Themed.Theme.backgroundColorLight
        duration: Themed.Theme.durationShort
        alwaysRunToEnd: true
        running: false
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true

        onContainsPressChanged: {
            if (containsPress) {
                toPressed.start()
            } else {
                toReleased.start()
            }
        }
        onClicked: tagClicked(text)
    }

    Row {
        id: contentsRow
        anchors.fill: parent
        anchors.leftMargin: Themed.Theme.spacingSmall
        anchors.rightMargin: Themed.Theme.spacingSmall
        spacing: 3

        Themed.Text {
            id: closeButton
            text: "✕"
            font.pointSize: Themed.Theme.textPointSize - 2
            color: Themed.Theme.textColor
            opacity: closeMouseArea.containsMouse ? 0.75 : 0.25
            Behavior on opacity {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}
            anchors.verticalCenter: parent.verticalCenter

            MouseArea {
                id: closeMouseArea
                anchors.fill: parent
                onClicked: tagClosed(tagText.text)
                hoverEnabled: true
            }
        }

        Themed.Text {
            id: tagText
            anchors.verticalCenter: parent.verticalCenter
        }
    }

}

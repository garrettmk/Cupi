import QtQuick 2.7

Item {
    id: root
    implicitWidth: 10
    implicitHeight: 10

    property int orientation: Qt.UpArrow
    property alias color: triangle.color

    Item {
        clip: true
        anchors.fill: parent
        anchors.bottomMargin: 1

        Rectangle {
            id: triangle
            rotation: 45
            width: Math.round(parent.width / Math.sqrt(2))
            height: width
            anchors {
                horizontalCenter: parent.horizontalCenter
                verticalCenter: root.orientation === Qt.UpArrow ? parent.bottom : parent.top
            }
        }
    }
}

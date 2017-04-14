import QtQuick 2.7
import QtQuick.Layouts 1.3
import "." as Themed

ListView {
    id: root
    clip: true
    focus: true
    spacing: 1
    orientation: ListView.Horizontal
    implicitWidth: 400
    implicitHeight: tabTitleMetrics.height + 2 * Themed.Theme.spacingSmall

    property real defaultTabOpacity: 0
    property int tabWidth: Math.max(root.width / model.length, 80)
    Behavior on tabWidth {
        NumberAnimation {duration: Themed.Theme.durationMid; easing.type: Easing.OutExpo}
    }

    property real tabOpacityMid: defaultTabOpacity + (1 - defaultTabOpacity) / 2

    // Signals
    signal tabCloseRequested(int index)

    // Text metrics: used to calculate the height of the delegates, since we don't
    // have direct access to them here.
    TextMetrics {
        id: tabTitleMetrics
        text: "..."
        font.pointSize: Themed.Theme.textPointSizeMid
    }

    // Tab delegate
    delegate: Item {
        id: delegate
        clip: true
        width: ListView.view.tabWidth
        height: ListView.view.height

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                delegate.ListView.view.currentIndex = index
            }
        }

        // Background rectangle
        Rectangle {
            id: delegateBackground
            gradient: Gradient {
                GradientStop {position: 0; color: Themed.Theme.backgroundColorLight}
                GradientStop {position: 1 - (delegateBackground.radius / height); color: "transparent"}
            }

            // don't hate
            opacity: delegate.ListView.isCurrentItem ? closeButton.hovered ? tabOpacityMid : 1 : mouseArea.containsMouse ? tabOpacityMid : defaultTabOpacity
            Behavior on opacity {NumberAnimation {duration: Themed.Theme.durationMid; easing.type: Themed.Theme.fadeEasingType}}

            radius: Themed.Theme.radiusMid
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
            }
            height: parent.height + radius
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: Themed.Theme.spacingSmall
            spacing: Themed.Theme.spacingSmall

            // Close button
            Themed.SmallButton {
                id: closeButton
                text: "✕"
                Layout.fillHeight: true
                Layout.preferredWidth: height
                opacity: mouseArea.containsMouse ? 0.5 : hovered ? 1 : 0
                Behavior on opacity {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}

                onClicked: root.tabCloseRequested(index)
            }
            // Tab title
            Themed.Text {
                id: tabTitle
                Layout.fillWidth: true
                rightPadding: closeButton.width + 2 * closeButton.anchors.margins
                text: title
                elide: Text.ElideRight
                font.bold: true
                font.pointSize: Themed.Theme.textPointSizeMid
                opacity: delegate.ListView.isCurrentItem ? 1 : 0.5
                Behavior on opacity {NumberAnimation {duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}}

                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}

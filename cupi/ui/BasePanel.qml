import QtQuick 2.7
import QtQuick.Layouts 1.3
import "." as QP

Rectangle {
    id:                 root
    color:              QP.Theme.backgroundColorMid
    radius:             QP.Theme.radiusMid
    border.width:       QP.Theme.borderWidthMid
    border.color:       QP.Theme.borderColorDark
    implicitWidth:      layout.implicitWidth + 2 * layout.anchors.margins
    implicitHeight:     layout.implicitHeight + 2 * layout.anchors.margins

    // Properties
    property int borderMargin: QP.Theme.spacingMid
    default property alias data: contentItem.data
    property alias content: contentItem.children
    property alias contentWidth:    contentItem.implicitWidth
    property alias contentHeight:   contentItem.implicitHeight

    property Item titleItem

    Component.onCompleted: {
        if (titleItem !== undefined && titleItem !== null) {
            titleItem.parent = titleItemHolder
            titleItem.anchors.left = titleItemHolder.left
            titleItem.anchors.right = titleItemHolder.right
        }
    }


    // Behaviors
    NumberAnimation {id: defaultAnimation; duration: QP.Theme.durationMid; easing.type: QP.Theme.defaultEasingType}
    Behavior on implicitWidth {animation: defaultAnimation}
    Behavior on implicitHeight {id: heightBehavior; animation: defaultAnimation}

    // States
    states: [
        State {
            name: "folded"
        },
        State {
            name: "unfolded"
        }
    ]

    // Transitions
    transitions: [
        Transition {
            to: "folded"
            SequentialAnimation {
                // Disable heightBehavior, it just adds lag
                PropertyAction {target: heightBehavior; property: "enabled"; value: false}

                // Shrink the separator, fade out the tools and contents
                ParallelAnimation {

                    // Separator
                    SequentialAnimation {
                        NumberAnimation {
                            target: separator
                            property: "width"
                            to: 0
                            easing.type: QP.Theme.defaultEasingType
                            duration: QP.Theme.durationMid
                        }
                        PropertyAction {
                            target: separator
                            property: "visible"
                            value: false
                        }
                    }

                    // Fade out the tools
                    NumberAnimation {
                        target: toolsItem
                        property: "opacity"
                        to: 0
                        easing.type: QP.Theme.fadeEasingType
                        duration: QP.Theme.durationShort
                    }

                    // Fade out the contents
                    NumberAnimation {
                        target: contentItem
                        property: "opacity"
                        to: 0
                        easing.type: QP.Theme.fadeEasingType
                        duration: QP.Theme.durationShort
                    }
                }

                // Shrink the content item
                ParallelAnimation {
                    NumberAnimation {
                        target: contentItem
                        property: "Layout.preferredHeight"
                        to: 0
                        easing.type: QP.Theme.defaultEasingType
                        duration: QP.Theme.durationMid
                    }

                    NumberAnimation {
                        target: contentItem
                        properties: "Layout.topMargin, Layout.bottomMargin"
                        to: 0
                        easing.type: QP.Theme.defaultEasingType
                        duration: QP.Theme.durationMid
                    }
                }
                PropertyAction {target: contentItem; property: "visible"; value: false}

                // Button label and cleanup
                PropertyAction {target: heightBehavior; property: "enabled"; value: true}
            }

        },
        Transition {
            to: "unfolded"
            SequentialAnimation {
                // Disable heightBehavior, it just adds lag
                PropertyAction {target: heightBehavior; property: "enabled"; value: false}

                // Grow the separator and the content item
                PropertyAction {target: contentItem; property: "visible"; value: true}
                ParallelAnimation {
                    // content item
                    ParallelAnimation {
                        NumberAnimation {
                            target: contentItem
                            property: "Layout.preferredHeight"
                            to: contentItem.implicitHeight
                            easing.type: QP.Theme.defaultEasingType
                            duration: QP.Theme.durationMid
                        }

                        NumberAnimation {
                            target: contentItem
                            properties: "Layout.topMargin"
                            to: QP.Theme.spacingMid + QP.Theme.spacingSmall - separator.height
                            easing.type: QP.Theme.defaultEasingType
                            duration: QP.Theme.durationMid
                        }

                        NumberAnimation {
                            target: contentItem
                            property: "Layout.bottomMargin"
                            to: QP.Theme.spacingSmall
                            easing.type: QP.Theme.defaultEasingType
                            duration: QP.Theme.durationMid
                        }
                    }
                }

                // Fade in the tools, separator and content item
                ParallelAnimation {
                    // Separator
                    SequentialAnimation {
                        PropertyAction {
                            target: separator
                            property: "visible"
                            value: true
                        }
                        NumberAnimation {
                            target: separator
                            property: "width"
                            from: 0
                            to: layout.width
                            easing.type: QP.Theme.defaultEasingType
                            duration: QP.Theme.durationMid
                        }
                    }

                    // tools
                    NumberAnimation {
                        target: toolsItem
                        property: "opacity"
                        to: 1
                        easing.type: QP.Theme.fadeEasingType
                        duration: QP.Theme.durationShort
                    }

                    // contents
                    NumberAnimation {
                        target: contentItem
                        property: "opacity"
                        to: 1
                        easing.type: QP.Theme.fadeEasingType
                        duration: QP.Theme.durationShort
                    }
                }

                // Button label and cleanup
                PropertyAction {target: heightBehavior; property: "enabled"; value: true}
            }
        }
    ]


    // Body
    ColumnLayout {
        id: layout
        spacing: 0
        anchors.fill: parent
        anchors.margins: root.border.width + root.borderMargin

        // Title item
        ColumnLayout {
            id:                     titleBarLayout
            clip:                   true
            spacing:                QP.Theme.spacingSmall
            visible:                root.titleItem !== undefined && root.titleItem !== null
            Layout.fillWidth:       true
            Layout.minimumHeight:   implicitHeight
            Layout.maximumHeight:   implicitHeight

            Item {
                id: titleItemHolder
                clip: true
                Layout.alignment: Qt.AlignBottom
                Layout.fillWidth: true
                Layout.maximumWidth: layout.width
                implicitWidth: children.length === 1 ? children[0].implicitWidth : childrenRect.width
                implicitHeight: children.length === 1 ? children[0].implicitHeight : childrenRect.height
            }

            // Separator line
            Rectangle {
                id: separator
                color: QP.Theme.borderColorDark
                radius: QP.Theme.radiusSmall
                Layout.preferredHeight: QP.Theme.borderWidthSmall
                Layout.preferredWidth: layout.width
            }
        }

        // Content area
        Item {
            id:                     contentItem
            clip:                   true
            implicitWidth:          contentItem.children.length === 1 ? contentItem.children[0].implicitWidth : contentItem.childrenRect.width
            implicitHeight:         contentItem.children.length === 1 ? contentItem.children[0].implicitHeight : contentItem.childrenRect.height
            Layout.fillWidth:       true
            Layout.fillHeight:      true
            Layout.preferredWidth:  implicitWidth
            Layout.preferredHeight: implicitHeight
            Layout.margins: QP.Theme.spacingSmall
            Layout.topMargin: root.titleItem !== undefined && root.titleItem !== null ? QP.Theme.spacingSmall + QP.Theme.spacingMid : QP.Theme.spacingSmall
        }
    }
}

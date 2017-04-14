import QtQuick 2.7
import QtQuick.Layouts 1.3
import "." as Themed

Rectangle {
    id:                 root
    color:              Themed.Theme.backgroundColorMid
    radius:             Themed.Theme.radiusMid
    border.width:       Themed.Theme.borderWidthMid
    border.color:       Themed.Theme.borderColorDark
    implicitWidth:      layout.implicitWidth + 2 * layout.anchors.margins
    implicitHeight:     layout.implicitHeight + 2 * layout.anchors.margins

    // Properties
    default property alias content: contentStack.children
    property alias contentWidth:    contentItem.implicitWidth
    property alias contentHeight:   contentItem.implicitHeight
    property alias title:           label.text
    property alias titlePointSize:  label.font.pointSize
    property alias tools:           toolsItem.children
    property bool folds:            true

    property alias currentIndex:    tabTitles.currentIndex
    property alias count:           contentStack.count
    property alias tabs:            contentStack.children

    property real defaultTabOpacity: 0

    // Signals
    signal tabCloseRequested(int index)

    // Methods
    function addTab(title, component) {
        var tab = Qt.createQmlObject("import QtQuick.Controls 1.4; Tab {title: \"" + title + "\"}", contentStack)
        if (component !== undefined) {
            tab.sourceComponent = component
        }
        currentIndex = content.length - 1
        return tab
    }

    function getTab(index) {
        if (index < count) {return content[index]}
        else {return null}
    }

    function removeTab(index) {
        var oldIndex = currentIndex
        var tab = content[index]
        tab.parent = null
        tab.destroy()
        currentIndex = Math.min(oldIndex, content.length - 1)
    }


    // Behaviors
    NumberAnimation {id: defaultAnimation; duration: Themed.Theme.durationMid; easing.type: Themed.Theme.defaultEasingType}
    Behavior on implicitWidth {animation: defaultAnimation}
    Behavior on implicitHeight {id: heightBehavior; animation: defaultAnimation}

    property int nextIndex
    SequentialAnimation {
        id: changeIndexAnimation
        NumberAnimation {
            target: contentStack
            property: "opacity"
            to: 0
            duration: Themed.Theme.durationMid / 2
            easing.type: Themed.Theme.fadeEasingType
        }
        ScriptAction {script: contentStack.currentIndex = nextIndex}
        NumberAnimation {
            target: contentStack
            property: "opacity"
            to: 1
            duration: Themed.Theme.durationMid / 2
            easing.type: Themed.Theme.fadeEasingType
        }
    }

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

                    // Temporarily fade out the expander button
                    NumberAnimation {
                        target: foldButton
                        property: "opacity"
                        to: 0
                        duration: Themed.Theme.durationShort
                        easing.type: Themed.Theme.fadeEasingType
                    }

                    // Separator
                    SequentialAnimation {
                        NumberAnimation {
                            target: separator
                            property: "width"
                            to: 0
                            easing.type: Themed.Theme.defaultEasingType
                            duration: Themed.Theme.durationMid
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
                        easing.type: Themed.Theme.fadeEasingType
                        duration: Themed.Theme.durationShort
                    }

                    // Fade out the tab titles
                    SequentialAnimation {
                        NumberAnimation {
                            target: tabTitles
                            property: "opacity"
                            to: 0
                            easing.type: Themed.Theme.fadeEasingType
                            duration: Themed.Theme.durationMid
                        }
                        PropertyAction {
                            target: tabTitles
                            property: "visible"
                            value: false
                        }
                    }

                    // Fade out the contents
                    NumberAnimation {
                        target: contentItem
                        property: "opacity"
                        to: 0
                        easing.type: Themed.Theme.fadeEasingType
                        duration: Themed.Theme.durationShort
                    }
                }

                // Shrink the content item
                ParallelAnimation {
                    NumberAnimation {
                        target: contentItem
                        property: "Layout.preferredHeight"
                        to: 0
                        easing.type: Themed.Theme.defaultEasingType
                        duration: Themed.Theme.durationMid
                    }

                    NumberAnimation {
                        target: contentItem
                        properties: "Layout.topMargin, Layout.bottomMargin"
                        to: 0
                        easing.type: Themed.Theme.defaultEasingType
                        duration: Themed.Theme.durationMid
                    }

                    // Fade in the title label
                    SequentialAnimation {
                        PropertyAction {
                            target: label
                            property: "visible"
                            value: true
                        }
                        NumberAnimation {
                            target: label
                            property: "opacity"
                            to: 1
                            easing.type: Themed.Theme.fadeEasingType
                            duration: Themed.Theme.durationShort
                        }
                    }

                    // Fade the expander button back in
                    NumberAnimation {
                        target: foldButton
                        property: "opacity"
                        to: 1
                        duration: Themed.Theme.durationShort
                        easing.type: Themed.Theme.fadeEasingType
                    }
                }

                // Button label and cleanup
                PropertyAction {target: foldButton; property: "text"; value: "＋"}
                PropertyAction {target: heightBehavior; property: "enabled"; value: true}
            }

        },
        Transition {
            to: "unfolded"
            SequentialAnimation {
                // Disable heightBehavior, it just adds lag
                PropertyAction {target: heightBehavior; property: "enabled"; value: false}

                // Grow the separator and the content item
                ParallelAnimation {

                    // Temporarily fade out the expander button
                    NumberAnimation {
                        target: foldButton
                        property: "opacity"
                        to: 0
                        duration: Themed.Theme.durationShort
                        easing.type: Themed.Theme.fadeEasingType
                    }

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
                            to: layout.width
                            easing.type: Themed.Theme.defaultEasingType
                            duration: Themed.Theme.durationMid
                        }
                    }

                    // Fade out the title label
                    SequentialAnimation {
                        NumberAnimation {
                            target: label
                            property: "opacity"
                            to: 0
                            easing.type: Themed.Theme.fadeEasingType
                            duration: Themed.Theme.durationShort
                        }
                        PropertyAction {
                            target: label
                            property: "visible"
                            value: false
                        }
                    }

                    // content item
                    ParallelAnimation {
                        NumberAnimation {
                            target: contentItem
                            property: "Layout.preferredHeight"
                            to: contentItem.implicitHeight
                            easing.type: Themed.Theme.defaultEasingType
                            duration: Themed.Theme.durationMid
                        }

                        NumberAnimation {
                            target: contentItem
                            properties: "Layout.topMargin"
                            to: Themed.Theme.spacingMid + Themed.Theme.spacingSmall - separator.height
                            easing.type: Themed.Theme.defaultEasingType
                            duration: Themed.Theme.durationMid
                        }

                        NumberAnimation {
                            target: contentItem
                            property: "Layout.bottomMargin"
                            to: Themed.Theme.spacingSmall
                            easing.type: Themed.Theme.defaultEasingType
                            duration: Themed.Theme.durationMid
                        }
                    }
                }

                // Fade in the tools and content item
                ParallelAnimation {

                    // tools
                    NumberAnimation {
                        target: toolsItem
                        property: "opacity"
                        to: 1
                        easing.type: Themed.Theme.fadeEasingType
                        duration: Themed.Theme.durationShort
                    }

                    // contents
                    NumberAnimation {
                        target: contentItem
                        property: "opacity"
                        to: 1
                        easing.type: Themed.Theme.fadeEasingType
                        duration: Themed.Theme.durationShort
                    }

                    // Fade in the tab titles
                    SequentialAnimation {
                        PropertyAction {
                            target: tabTitles
                            property: "visible"
                            value: true
                        }

                        NumberAnimation {
                            target: tabTitles
                            property: "opacity"
                            to: 1
                            easing.type: Themed.Theme.fadeEasingType
                            duration: Themed.Theme.durationShort
                        }
                    }

                    // Fade the expander button back in
                    NumberAnimation {
                        target: foldButton
                        property: "opacity"
                        to: 1
                        duration: Themed.Theme.durationShort
                        easing.type: Themed.Theme.fadeEasingType
                    }
                }

                // Button label and cleanup
                PropertyAction {target: foldButton; property: "text"; value: "－"}
                PropertyAction {target: heightBehavior; property: "enabled"; value: true}
            }
        }
    ]


    // Body
    ColumnLayout {
        id:                         layout
        spacing: 0
        anchors.fill:               parent
        anchors.margins:            Themed.Theme.spacingMid

        // Title item
        ColumnLayout {
            id:                     titleItem
            clip:                   true
            spacing:                1//Themed.Theme.spacingSmall
            visible:                root.title ? true : false
            Layout.fillWidth:       true

            RowLayout {
                spacing:                Themed.Theme.spacingSmall
                Layout.fillWidth:       true
                Layout.minimumHeight:   implicitHeight
                Layout.maximumHeight:   implicitHeight

                // Title text
                Themed.Text {
                    id:             label
                    visible:        false
                    verticalAlignment:  Text.AlignBottom
                    Layout.alignment:  Qt.AlignVCenter
                    font.bold: true
                    font.pointSize: Themed.Theme.textPointSizeMid
                }

                // Tab titles
                Themed.TabHeaderList {
                    id: tabTitles
                    Layout.fillWidth: true
                    Layout.preferredHeight: implicitHeight
                    model: contentStack.children
                    defaultTabOpacity: root.defaultTabOpacity

                    onCurrentIndexChanged: {
                        root.nextIndex = currentIndex
                        changeIndexAnimation.start()
                    }

                    onTabCloseRequested: root.tabCloseRequested(index)
                }

                // Fold button
                Themed.SmallButton {
                    id: foldButton
                    text: "－"
                    visible: root.folds
                    Layout.preferredWidth: 18
                    Layout.preferredHeight: 18

                    onClicked: {
                        if (root.state === "folded") {
                            root.state = "unfolded"
                        } else {
                            root.state = "folded"
                        }
                    }
                }

                // Tools item
                Item {
                    id: toolsItem
                    Layout.preferredHeight: childrenRect.height
                    Layout.preferredWidth: childrenRect.width
                }
            }

            // Separator line
            Rectangle {
                id: separator
                color: Themed.Theme.borderColorDark
                radius: Themed.Theme.radiusSmall
                Layout.preferredHeight: Themed.Theme.borderWidthSmall
                Layout.preferredWidth: layout.width
            }
        }

        // Content area
        Item {
            id:                     contentItem
            clip:                   root.folds
            implicitWidth:          childrenRect.width
            implicitHeight:         childrenRect.height

            Layout.fillWidth:       true
            Layout.fillHeight:      true
            Layout.preferredWidth:  implicitWidth
            Layout.preferredHeight: implicitHeight
            Layout.topMargin:       Themed.Theme.spacingMid + Themed.Theme.spacingSmall - separator.height
            Layout.leftMargin:      Themed.Theme.spacingSmall
            Layout.rightMargin:     Themed.Theme.spacingSmall
            Layout.bottomMargin:    Themed.Theme.spacingSmall

            StackLayout {
                id:                 contentStack
                anchors.fill:       parent
            }
        }
    }
}

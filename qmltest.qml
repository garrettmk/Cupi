import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Window 2.2
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.0
import cupi.ui 1.0 as Themed

Window {
    id:                 root
    title:              "QML Test"
    visible:            true

    width:              1200
    height:             1000

    Themed.ThemeEditor {
        id: testDialog
    }

    Rectangle {
        anchors.fill: parent
        color: Themed.Theme.backgroundColor

        Themed.ToolBar {
            id: testToolBar
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
            }

            RowLayout {
                anchors.fill: parent
                Themed.Button {text: "Button"}
                Item {Layout.fillWidth: true}
            }
        }

        Flow {
            id: testArea
            anchors {
                fill: parent
                margins: Themed.Theme.spacingBig
                topMargin: testToolBar.height + Themed.Theme.spacingBig
                bottomMargin: testStatusBar.height + Themed.Theme.spacingBig
            }

            spacing: Themed.Theme.spacingBig
            flow: Flow.TopToBottom

            property int panelWidth: (width - spacing) / 2

            Themed.Panel {
                width: testArea.panelWidth
                contentHeight: 200

                Rectangle {
                    color: Themed.Theme.highlightColor
                    anchors.fill: parent

                    Themed.Text {
                        text: "A fixed panel with no title."
                        anchors.centerIn: parent
                    }
                }
            }

            Themed.Panel {
                title: "Button Types"
                width: testArea.panelWidth
                contentHeight: layout1.implicitHeight

                tools: Row {
                    spacing: 1
                    Themed.SmallButton {text: "Tool"}
                    Themed.SmallButton {text: "buttons"}
                }

                Column {
                    id: layout1
                    spacing: Themed.Theme.spacingMid
                    anchors.fill: parent

                    Row {
                        spacing: Themed.Theme.spacingMid
                        anchors.horizontalCenter: parent.horizontalCenter
                        Themed.Button {
                            text: "Regular"
                        }
                        Themed.Button {
                            text: "Buttons"
                            onClicked: testDialog.show()
                        }
                    }

                    Row {
                        spacing: Themed.Theme.spacingSmall
                        anchors.horizontalCenter: parent.horizontalCenter

                        Themed.SmallButton {text: "These"}
                        Themed.SmallButton {text: "are"}
                        Themed.SmallButton {text: "small"}
                        Themed.SmallButton {text: "buttons."}
                    }

                    Row {
                        spacing: Themed.Theme.spacingMid
                        anchors.horizontalCenter: parent.horizontalCenter

                        Column {
                            spacing: Themed.Theme.spacingSmall

                            Themed.CheckBox {text: "Check"; checked: true}
                            Themed.CheckBox {text: "Boxes"}
                        }

                        Column {
                            spacing: Themed.Theme.spacingSmall
                            ExclusiveGroup {id: ex}
                            Themed.RadioButton {text: "Radio"; exclusiveGroup: ex}
                            Themed.RadioButton {text: "Buttons"; exclusiveGroup: ex}
                        }
                    }
                }
            }

            Themed.Panel {
                title: "Input Elements"
                width: testArea.panelWidth
                contentHeight: inputLayout.implicitHeight

                GridLayout {
                    id: inputLayout
                    columns: 2
                    rowSpacing: Themed.Theme.spacingMid
                    columnSpacing: Themed.Theme.spacingMid

                    anchors.fill: parent

                    Themed.Text {text: "SpinBox:"; Layout.alignment: Qt.AlignRight}
                    Themed.SpinBox {minimumValue: -10; maximumValue: 10; decimals: 1}

                    Themed.Text {text: "PercentBox:"; Layout.alignment: Qt.AlignRight}
                    Themed.PercentBox {value: 55}

                    Themed.Text {text: "PriceBox:"; Layout.alignment: Qt.AlignRight}
                    Themed.PriceBox {value: 55.98}

                    Themed.Text {text: "ComboBox:"; Layout.alignment: Qt.AlignRight}
                    Themed.ComboBox {model: ["Pick", "One", "Option"]}

                    Themed.Text {text: "Read-only ComboBox:"; Layout.alignment: Qt.AlignRight}
                    Themed.ComboBox {model: ["Read-Only"]; enabled: false}
                }
            }

            Themed.Panel {
                title: "Tags"
                width: testArea.panelWidth
                contentHeight: tagEditor.implicitHeight

                tools: Row {
                    Themed.SmallButton {text: tagEditor.enabled ? "Disable" : "Enable"; onClicked: tagEditor.enabled = !tagEditor.enabled}
                    Themed.SmallButton {text: "Clear"; onClicked: tagEditor.clear()}
                    Themed.SmallButton {text: "Reset"; onClicked: tagEditor.setTags(["These", "are", "all", "tags."])}
                }

                Themed.TagEditor {
                    id: tagEditor
                    anchors.fill: parent
                    onTagClosed: console.log(tag)
                    onTagClicked: console.log(tag)

                    Component.onCompleted: {
                        setTags(["These", "are", "all", "tags"])
                    }
                }
            }

            Themed.Panel {
                title: "Text Elements"
                width: testArea.panelWidth
                contentHeight: textElementsLayout.implicitHeight

                ColumnLayout {
                    id: textElementsLayout
                    spacing: Themed.Theme.spacingMid
                    anchors.fill: parent

                    Themed.Text {
                        text: "This is a Themed Text element. It is a read-only element, and does not support selection."
                        wrapMode: Text.WordWrap
                        Layout.fillHeight: true
                        Layout.fillWidth: true

                    }

                    Themed.Text {text: "Here are some elements that support text input:"}

                    GridLayout {
                        columns: 2
                        rowSpacing: Themed.Theme.spacingSmall
                        columnSpacing: Themed.Theme.spacingSmall
                        Layout.fillWidth: true
                        Layout.preferredHeight: implicitHeight
                        Layout.preferredWidth: implicitWidth

                        Themed.Text {text: "TextField:"; Layout.alignment: Qt.AlignRight}
                        Themed.TextField {placeholderText: "Placeholder text"; Layout.fillWidth: true}
                        Themed.Text {text: "TextField:"; Layout.alignment: Qt.AlignRight}
                        Themed.TextField {text: "Regular, selectable text."; Layout.fillWidth: true}
                        Themed.Text {text: "TextField:"; Layout.alignment: Qt.AlignRight}
                        Themed.TextField {
                            text: "Text that has been selected."
                            Layout.fillWidth: true
                            Component.onCompleted: selectAll()
                        }
                    }
                }
            }

            Themed.Panel {
                title: "Text Areas"
                width: testArea.panelWidth
                contentHeight: 250

                Themed.TextArea {
                    text: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam at ex in enim auctor cursus non ultricies libero. Suspendisse gravida odio arcu, eget semper quam iaculis nec. Nunc id finibus felis. Maecenas faucibus mattis dui, quis accumsan ligula sagittis in. Maecenas bibendum nisi massa, ac consectetur leo facilisis et. Pellentesque eget erat mi. Pellentesque sapien neque, auctor dictum arcu nec, viverra egestas risus. Nulla malesuada ullamcorper urna quis elementum. Maecenas posuere varius orci, in porttitor nisl porta nec. Nunc scelerisque lectus vel augue pellentesque imperdiet. Praesent lectus ex, placerat in tempor vel, tristique eget nunc. Aenean sollicitudin mattis ex. Vestibulum nulla ligula, rhoncus vitae sapien in, ornare sollicitudin neque. Phasellus vitae mollis ante."
                    anchors.fill: parent
                }
            }

            Themed.TabView {
                id: tabView
                title: "TabView"
                width: testArea.panelWidth
                contentHeight: 250

                tools: Themed.SmallButton {
                    text: "Add"
                    onClicked: tabView.addTab("New Tab")
                }

                onTabCloseRequested: {
                    removeTab(index)
                }

                Tab {
                    title: "One"
                    Themed.Text {text: "One"}
                }
                Tab {
                    title: "Two"
                    Themed.Text {text: "Two"}
                }
                Tab {
                    title: "Three"
                    Themed.Text {text: "Three"}
                }
            }
        }

        Themed.StatusBar {
            id: testStatusBar
            anchors {
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }

            Themed.Text {text: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}
        }
    }


    ColorDialog {
        id:                 colorDialog
        title:              "Select a color"

        property var oldColor
        property string boundColor: ""

        function bindToColor(name) {
            if (boundColor) {
                oldColor = currentColor
                console.log(oldColor)
                unbindColor()
            }
            colorDialog.currentColor = Themed.Theme[name]
            colorDialog.oldColor = Themed.Theme[name]
            colorDialog.color = Themed.Theme[name]
            Themed.Theme[name] = Qt.binding(function() {return colorDialog.currentColor})
            boundColor = name
        }

        function unbindColor() {
            Themed.Theme[boundColor] = oldColor
            boundColor = ""
        }

        onAccepted: unbindColor()
        onRejected: {
            unbindColor()
        }
    }

}

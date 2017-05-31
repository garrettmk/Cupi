import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Window 2.2
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.0
import cupi.ui 1.0 as QP

Window {
    id:                 root
    title:              "QML Test"
    visible:            true

    width:              1200
    height:             1000

    QP.ThemeEditor {
        id: testDialog
    }

    Rectangle {
        anchors.fill: parent
        color: QP.Theme.backgroundColor

        QP.ToolBar {
            id: testToolBar
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
            }

            RowLayout {
                anchors.fill: parent
                QP.Button {text: "Button"}
                Item {Layout.fillWidth: true}
            }
        }

        Flow {
            id: testArea
            anchors {
                fill: parent
                margins: QP.Theme.spacingBig
                topMargin: testToolBar.height + QP.Theme.spacingBig
                bottomMargin: testStatusBar.height + QP.Theme.spacingBig
            }

            spacing: QP.Theme.spacingBig
            flow: Flow.TopToBottom

            property int panelWidth: (width - spacing) / 2

            QP.BasePanel {
                width: testArea.panelWidth
                contentHeight: 200

                Rectangle {
                    color: QP.Theme.highlightColor
                    anchors.fill: parent

                    QP.Text {
                        text: "A fixed panel with no title."
                        anchors.centerIn: parent
                    }
                }
            }

            QP.Panel {
                title: "Button Types"
                width: testArea.panelWidth
                contentHeight: layout1.implicitHeight

                tools: Row {
                    spacing: 1
                    QP.SmallButton {text: "Tool"}
                    QP.SmallButton {text: "buttons"}
                }

                Column {
                    id: layout1
                    spacing: QP.Theme.spacingMid
                    anchors.fill: parent

                    Row {
                        spacing: QP.Theme.spacingMid
                        anchors.horizontalCenter: parent.horizontalCenter
                        QP.Button {
                            text: "Regular"
                        }
                        QP.Button {
                            text: "Buttons"
                            onClicked: testDialog.show()
                        }
                    }

                    Row {
                        spacing: QP.Theme.spacingSmall
                        anchors.horizontalCenter: parent.horizontalCenter

                        QP.SmallButton {text: "These"}
                        QP.SmallButton {text: "are"}
                        QP.SmallButton {text: "small"}
                        QP.SmallButton {text: "buttons."}
                    }

                    Row {
                        spacing: QP.Theme.spacingMid
                        anchors.horizontalCenter: parent.horizontalCenter

                        Column {
                            spacing: QP.Theme.spacingSmall

                            QP.CheckBox {text: "Check"; checked: true}
                            QP.CheckBox {text: "Boxes"}
                        }

                        Column {
                            spacing: QP.Theme.spacingSmall
                            ExclusiveGroup {id: ex}
                            QP.RadioButton {text: "Radio"; exclusiveGroup: ex}
                            QP.RadioButton {text: "Buttons"; exclusiveGroup: ex}
                        }
                    }
                }
            }

            QP.Panel {
                title: "Input Elements"
                width: testArea.panelWidth
                contentHeight: inputLayout.implicitHeight

                GridLayout {
                    id: inputLayout
                    columns: 2
                    rowSpacing: QP.Theme.spacingMid
                    columnSpacing: QP.Theme.spacingMid

                    anchors.fill: parent

                    QP.Text {text: "SpinBox:"; Layout.alignment: Qt.AlignRight}
                    QP.SpinBox {minimumValue: -10; maximumValue: 10; decimals: 1}

                    QP.Text {text: "PercentBox:"; Layout.alignment: Qt.AlignRight}
                    QP.PercentBox {value: 55}

                    QP.Text {text: "PriceBox:"; Layout.alignment: Qt.AlignRight}
                    QP.PriceBox {value: 55.98}

                    QP.Text {text: "ComboBox:"; Layout.alignment: Qt.AlignRight}
                    QP.ComboBox {model: ["Pick", "One", "Option"]}

                    QP.Text {text: "Read-only ComboBox:"; Layout.alignment: Qt.AlignRight}
                    QP.ComboBox {model: ["Read-Only"]; enabled: false}
                }
            }

            QP.Panel {
                title: "Tags"
                width: testArea.panelWidth
                contentHeight: tagEditor.implicitHeight

                tools: Row {
                    QP.SmallButton {text: tagEditor.enabled ? "Disable" : "Enable"; onClicked: tagEditor.enabled = !tagEditor.enabled}
                    QP.SmallButton {text: "Clear"; onClicked: tagEditor.clear()}
                    QP.SmallButton {text: "Reset"; onClicked: tagEditor.setTags(["These", "are", "all", "tags."])}
                }

                QP.TagEditor {
                    id: tagEditor
                    anchors.fill: parent

                    Component.onCompleted: {
                        setTags(["These", "are", "all", "tags"])
                    }
                }
            }

            QP.Panel {
                title: "Text Elements"
                width: testArea.panelWidth
                contentHeight: textElementsLayout.implicitHeight

                ColumnLayout {
                    id: textElementsLayout
                    spacing: QP.Theme.spacingMid
                    anchors.fill: parent

                    QP.Text {
                        text: "This is a Themed Text element. It is a read-only element, and does not support selection."
                        wrapMode: Text.WordWrap
                        Layout.fillHeight: true
                        Layout.fillWidth: true

                    }

                    QP.Text {text: "Here are some elements that support text input:"}

                    GridLayout {
                        columns: 2
                        rowSpacing: QP.Theme.spacingSmall
                        columnSpacing: QP.Theme.spacingSmall
                        Layout.fillWidth: true
                        Layout.preferredHeight: implicitHeight
                        Layout.preferredWidth: implicitWidth

                        QP.Text {text: "TextField:"; Layout.alignment: Qt.AlignRight}
                        QP.TextField {placeholderText: "Placeholder text"; Layout.fillWidth: true}
                        QP.Text {text: "TextField:"; Layout.alignment: Qt.AlignRight}
                        QP.TextField {text: "Regular, selectable text."; Layout.fillWidth: true}
                        QP.Text {text: "TextField:"; Layout.alignment: Qt.AlignRight}
                        QP.TextField {
                            text: "Text that has been selected."
                            Layout.fillWidth: true
                            Component.onCompleted: selectAll()
                        }
                    }
                }
            }

            QP.Panel {
                title: "Text Areas"
                width: testArea.panelWidth
                contentHeight: 250

                QP.TextArea {
                    text: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam at ex in enim auctor cursus non ultricies libero. Suspendisse gravida odio arcu, eget semper quam iaculis nec. Nunc id finibus felis. Maecenas faucibus mattis dui, quis accumsan ligula sagittis in. Maecenas bibendum nisi massa, ac consectetur leo facilisis et. Pellentesque eget erat mi. Pellentesque sapien neque, auctor dictum arcu nec, viverra egestas risus. Nulla malesuada ullamcorper urna quis elementum. Maecenas posuere varius orci, in porttitor nisl porta nec. Nunc scelerisque lectus vel augue pellentesque imperdiet. Praesent lectus ex, placerat in tempor vel, tristique eget nunc. Aenean sollicitudin mattis ex. Vestibulum nulla ligula, rhoncus vitae sapien in, ornare sollicitudin neque. Phasellus vitae mollis ante."
                    anchors.fill: parent
                }
            }

            QP.TabView {
                id: tabView
                title: "TabView"
                width: testArea.panelWidth
                contentHeight: 250

                tools: QP.SmallButton {
                    text: "Add"
                    onClicked: tabView.addTab("New Tab")
                }

                onTabCloseRequested: {
                    removeTab(index)
                }

                Tab {
                    title: "Lists"
                    QP.Button {
                        text: "Test"
                        onClicked: {
                            console.log(test_object.listProp)
                            console.log(test_object.listProp[1])
                        }
                    }
                }
                Tab {
                    title: "Two"
                    QP.Text {text: "Two"}
                }
                Tab {
                    title: "Three"
                    QP.Text {text: "Three"}
                }
            }
        }

        QP.StatusBar {
            id: testStatusBar
            anchors {
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }

            QP.Text {text: "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}
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
            colorDialog.currentColor = QP.Theme[name]
            colorDialog.oldColor = QP.Theme[name]
            colorDialog.color = QP.Theme[name]
            QP.Theme[name] = Qt.binding(function() {return colorDialog.currentColor})
            boundColor = name
        }

        function unbindColor() {
            QP.Theme[boundColor] = oldColor
            boundColor = ""
        }

        onAccepted: unbindColor()
        onRejected: {
            unbindColor()
        }
    }

}

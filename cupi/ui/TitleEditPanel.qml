import QtQuick 2.7
import QtQuick.Layouts 1.3
import "." as QP

QP.BasePanel {
    id: root
    titleItem: RowLayout {
        id: titleLayout
        spacing: QP.Theme.spacingSmall
        anchors {
            right: parent.right
            left: parent.left
        }

        // Title text
        Item {
            id: titleTextHolder
            clip: true
            Layout.alignment: Qt.AlignBottom
            Layout.fillWidth: true
            implicitHeight: titleTextField.height - QP.Theme.borderWidthSmall

            StackLayout {
                currentIndex: titleTextField.activeFocus
                implicitHeight: titleTextField.implicitHeight
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                }

                QP.Text {
                    id: titleTextLabel
                    elide: Qt.ElideMiddle
                    font: titleTextField.font
                    text: titleTextField.text

                    MouseArea {
                        anchors.fill: parent
                        onDoubleClicked: titleTextField.forceActiveFocus()
                    }
                }

                QP.TextField {
                    id: titleTextField
                    readOnly: root.state === "folded"

                    FontMetrics {
                        id: titleFontMetrics
                        font: titleTextField.font
                    }

                    onEditingFinished: {
                        root.titleEditingFinished(text)
                    }
                }
            }
        }

        // Tools item
        Item {
            id: toolsItem
            visible: children.length > 0
            Layout.alignment: Qt.AlignBottom
            Layout.preferredWidth: children.length === 1 ? children[0].implicitWidth : childrenRect.width
            Layout.preferredHeight: children.length === 1 ? children[0].implicitHeight : childrenRect.height
        }

        // Fold button
        QP.FoldButton {
            id: foldButton
            folded: root.state === "folded"
            visible: root.folds
            Layout.alignment: Qt.AlignBottom

            onClicked: {
                if (root.state === "folded") {
                    root.state = "unfolded"
                } else {
                    root.state = "folded"
                }
            }
        }
    }

    // Properties
    property alias title: titleTextField.text
    property alias titlePointSize: titleTextField.font.pointSize
    property alias tools: toolsItem.children
    property alias folds: foldButton.visible

    // Signals
    signal titleEditingFinished(string newTitle)
}

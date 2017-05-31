import QtQuick 2.7
import QtQuick.Layouts 1.3
import "." as QP

QP.BasePanel {
    id: root
    titleItem: RowLayout {
        spacing: QP.Theme.spacingSmall

        // Title text
        Item {
            clip: true
            implicitWidth: titleLabel.implicitWidth
            implicitHeight: titleMetrics.tightBoundingRect.height + 3
            Layout.fillWidth: true

            QP.Text {
                id: titleLabel
                font.bold: true
                font.pointSize: QP.Theme.textPointSizeMid
                anchors {
                    left: parent.left
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                }

                TextMetrics {
                    id: titleMetrics
                    font: titleLabel.font
                    text: titleLabel.text
                }
            }
        }

        Item {Layout.fillWidth: true}

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
    property alias title: titleLabel.text
    property alias titlePointSize: titleLabel.font.pointSize
    property alias tools: toolsItem.children
    property alias folds: foldButton.visible
}

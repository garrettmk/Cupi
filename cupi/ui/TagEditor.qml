import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import "." as QP

Item {
    id: root
    implicitWidth: flow.implicitWidth
    implicitHeight: flow.implicitHeight

    property alias model: repeater.model
    property alias delegate: repeater.delegate

    signal tagsChanged()
    signal tagClicked(string tag)

    // Methods
    function addTag(tag) {
        model.append({"tag": tag})
        tagsChanged()
    }

    function removeTag(index) {
        repeater.model.remove(index, 1)
        tagsChanged()
    }

    function clear() {
        repeater.model.clear()
    }

    function setTags(tags) {
        repeater.model.clear()
        for (var i=0; i<tags.length; i++) {
            repeater.model.append({"tag": tags[i]})
        }
    }

    function getTags() {
        var tags = []
        for (var i=0; i<repeater.model.count; i++) {
            tags.push(repeater.model.get(i)["tag"])
        }
        return tags
    }

    TextMetrics {
        id: textMetrics
        font.pointSize: textField.font.pointSize
        text: textField.text + "______"
    }

    // Body
    Flow {
        id: flow
        spacing: QP.Theme.spacingSmall
        anchors.fill: parent

        Repeater {
            id: repeater
            model: ListModel {}
            delegate: QP.TagDelegate {
                text: tag
                onTagClosed: {
                    removeTag(index)
                }
                onTagClicked: {
                    root.tagClicked(modelData)
                }
            }
        }

        QP.TextField {
            id: textField
            visible: root.enabled
            implicitWidth: textMetrics.width
            onEditingFinished: {
                if (text !== "") {
                    root.addTag(textField.text.trim())
                    textField.text = ""
                }
            }
        }

        add: Transition {
            SequentialAnimation {
                PropertyAction {property:"opacity"; value: 0}
                PauseAnimation {
                    duration: QP.Theme.durationMid
                }
                NumberAnimation {property: "opacity"; from: 0; to: 1; duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}
            }

        }

        move: Transition {
            id: moveTrans
            ParallelAnimation {
                NumberAnimation {property: "opacity"; from: 0; to: 1; duration: QP.Theme.durationMid; easing.type: QP.Theme.fadeEasingType}
                NumberAnimation {properties: "x,y"; duration: QP.Theme.durationMid; easing.type: QP.Theme.defaultEasingType}
            }
        }
    }
}

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import "." as Themed

Item {
    id: root
    implicitWidth: flow.implicitWidth
    implicitHeight: flow.implicitHeight

    property alias model: repeater.model
    property alias delegate: repeater.delegate

    signal newTag(string tag)
    signal tagClosed(string tag)
    signal tagClicked(string tag)

    // Default signal handler
    onNewTag: {console.log(model); addTag(tag)}

    // Methods
    function addTag(tag) {
        model.append({"tag": tag})
    }

    function removeTag(index) {
        repeater.model.remove(index, 1)
    }

    function clear() {
        repeater.model.clear()
    }

    function setTags(tags) {
        repeater.model.clear()
        for (var i=0; i<tags.length; i++) {
            repeater.model.append({"tags": tags[i]})
        }
    }

    TextMetrics {
        id: textMetrics
        font.pointSize: textField.font.pointSize
        text: textField.text + "______"
    }

    // Body
    Flow {
        id: flow
        spacing: Themed.Theme.spacingSmall
        anchors.fill: parent

        Repeater {
            id: repeater
            model: ListModel {}
            delegate: Themed.TagDelegate {
                text: tag
                onTagClosed: {
                    root.tagClosed(modelData)
                    repeater.model.remove(index, 1)
                }
                onTagClicked: {
                    root.tagClicked(modelData)
                }
            }
        }

        Themed.TextField {
            id: textField
            visible: root.enabled
            implicitWidth: textMetrics.width
            onEditingFinished: {
                if (text !== "") {
                    root.newTag(textField.text.trim())
                    textField.text = ""
                }
            }
        }

        add: Transition {
            SequentialAnimation {
                PropertyAction {property:"opacity"; value: 0}
                PauseAnimation {
                    duration: Themed.Theme.durationMid
                }
                NumberAnimation {property: "opacity"; from: 0; to: 1; duration: Themed.Theme.durationShort; easing.type: Themed.Theme.fadeEasingType}
            }

        }

        move: Transition {
            id: moveTrans
            ParallelAnimation {
                NumberAnimation {property: "opacity"; from: 0; to: 1; duration: Themed.Theme.durationMid; easing.type: Themed.Theme.fadeEasingType}
                NumberAnimation {properties: "x,y"; duration: Themed.Theme.durationMid; easing.type: Themed.Theme.defaultEasingType}
            }
        }
    }
}

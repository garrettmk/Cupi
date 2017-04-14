import QtQuick 2.7
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.0
import "." as QP


QP.Dialog {
    id: root
    title: "Cupi Theme Editor"
    width: colorsTab.implicitWidth
    height: tabs.implicitHeight + colorsTab.implicitHeight + 25

    Component.onCompleted: {
        minimumWidth = width
        minimumHeight = height
    }

    // Color chooser dialog
    ColorDialog {
        id:                 colorDialog
        title:              "Select a color"

        property var oldColor
        property string boundColor: ""

        function bindToColor(name) {
            if (boundColor) {
                oldColor = currentColor
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

    // Body
    QP.TabView {
        id: tabs
        title: "Cupi Theme Editor"
        folds: false
        radius: 0
        color: QP.Theme.backgroundColor
        anchors.fill: parent
        border.width: QP.Theme.borderWidthBig
        titlePointSize: QP.Theme.textPointSizeBig
        defaultTabOpacity: 0.5

       Tab {
           id: colorsTab
           title: "Colors"
           active: true

           property int selectedColorIndex: 0

           QP.Panel {
               ColumnLayout {
                   id: colorsTabLayout
                   anchors.fill: parent
                   spacing: QP.Theme.spacingMid

                   RowLayout {
                       Layout.fillWidth: true

                       Repeater {
                           model: [
                               "backgroundColor",
                               "backgroundColorMid",
                               "backgroundColorLight",
                               "borderColor",
                               "borderColorDark",
                               "highlightColor",
                               "textColor",
                               "selectedTextColor"
                           ]

                           ColumnLayout {
                               Layout.fillWidth: true
                               Layout.fillHeight: true
                               spacing: QP.Theme.spacingSmall

                               QP.Text {
                                   text: modelData + ":"
                                   font.bold: colorsTab.selectedColorIndex === index
                                   Layout.fillWidth: true
                                   horizontalAlignment: Text.AlignHCenter
                               }

                               QP.TextField {
                                   text: QP.Theme[modelData]
                                   onEditingFinished: QP.Theme[modelData] = text
                                   Layout.alignment: Qt.AlignCenter
                                   horizontalAlignment: Text.AlignHCenter
                                   font.capitalization: Font.AllUppercase
                               }

                               Rectangle {
                                   color: QP.Theme[modelData]
                                   radius: QP.Theme.radiusSmall
                                   border.color: Qt.rgba(1, 1, 1, borderAlpha)
                                   border.width: 3
                                   Layout.fillWidth: true
                                   Layout.fillHeight: true
                                   implicitWidth: 150
                                   implicitHeight: 250

                                   property real borderAlpha: colorsTab.selectedColorIndex === index ? 1 : colorMouseArea.containsMouse ? 0.5 : 0
                                   Behavior on borderAlpha {NumberAnimation {duration: QP.Theme.durationShort; easing.type: QP.Theme.fadeEasingType}}

                                   MouseArea {
                                       id: colorMouseArea
                                       anchors.fill: parent
                                       hoverEnabled: true
                                       onClicked: {
                                           colorsTab.selectedColorIndex = index
                                           colorDialog.bindToColor(modelData)
                                       }
                                       onDoubleClicked: {
                                           colorDialog.open()
                                       }
                                   }
                               }
                           }

                       }
                   }
               }
           }
       }

       Tab {
           id: dimensionsTab
           title: "Dimensions"

           Flow {
               id: dimensionsTabLayout
               flow: Flow.TopToBottom
               spacing: QP.Theme.spacingBig
               anchors.fill: parent

               property int panelWidth: (width - spacing) / 2
               property int panelHeight: (height - spacing) / 2

               QP.Panel {
                   title: "Text Sizes"
                   width: panelWidth

                   ColumnLayout {
                       anchors.centerIn: parent

                       Repeater {
                           model: [
                               "textPointSize",
                               "textPointSizeSmall",
                               "textPointSizeMid",
                               "textPointSizeBig",
                           ]

                           RowLayout {
                               spacing: QP.Theme.spacingMid

                               QP.Text {
                                   text: modelData + ": "
                                   horizontalAlignment: Text.AlignRight
                                   Layout.alignment: Qt.AlignRight
                                   Layout.preferredWidth: 150
                               }

                               QP.SpinBox {
                                   value: QP.Theme[modelData]
                                   minimumValue: 0
                                   maximumValue: 100
                                   onValueChanged: QP.Theme[modelData] = value
                               }

                               QP.Text {
                                   text: "Lorem ipsum"
                                   elide: Text.ElideRight
                                   font.pointSize: QP.Theme[modelData]
                               }
                           }
                       }
                   }
               }

               QP.Panel {
                   title: "Spacing Sizes"
                   width: panelWidth

                   ColumnLayout {
                       anchors.centerIn: parent

                       Repeater {
                           model: [
                               "spacingSmall",
                               "spacingMid",
                               "spacingBig"
                           ]

                           RowLayout {
                               spacing: QP.Theme.spacingMid

                               QP.Text {
                                   text: modelData + ": "
                                   horizontalAlignment: Text.AlignRight
                                   Layout.alignment: Qt.AlignRight
                                   Layout.preferredWidth: 150
                               }

                               QP.SpinBox {
                                   value: QP.Theme[modelData]
                                   minimumValue: 0
                                   maximumValue: 100
                                   onValueChanged: QP.Theme[modelData] = value
                               }

                               Row {
                                   spacing: QP.Theme[modelData]
                                   Layout.preferredHeight: parent.height

                                   Repeater {
                                       model: 2
                                       Rectangle {
                                           color: QP.Theme.borderColor
                                           width: parent.height
                                           height: parent.height
                                           radius: QP.Theme.radiusSmall
                                       }
                                   }
                               }
                           }
                       }
                   }
               }

               QP.Panel {
                   title: "Radius Sizes"
                   width: panelWidth

                   ColumnLayout {
                       anchors.centerIn: parent

                       Repeater {
                           id: radiusRepeater
                           model: [
                               "radiusSmall",
                               "radiusMid",
                               "radiusBig"
                           ]

                           RowLayout {
                               spacing: QP.Theme.spacingMid

                               QP.Text {
                                   text: modelData + ": "
                                   horizontalAlignment: Text.AlignRight
                                   Layout.alignment: Qt.AlignRight
                                   Layout.preferredWidth: 150
                               }

                               QP.SpinBox {
                                   value: QP.Theme[modelData]
                                   minimumValue: 0
                                   maximumValue: 100
                                   onValueChanged: QP.Theme[modelData] = value
                               }

                               Item {
                                   Layout.preferredWidth: Math.max(QP.Theme[modelData] * 2, parent.height)
                                   Layout.preferredHeight: Layout.preferredWidth
                                   clip: true
                                   Rectangle {
                                       width: parent.width + radius
                                       height: parent.height + radius
                                       anchors.bottom: parent.bottom
                                       anchors.left: parent.left
                                       color: "transparent"
                                       border.color: QP.Theme.borderColor
                                       radius: QP.Theme[modelData]
                                   }
                               }
                           }
                       }
                   }
               }

               QP.Panel {
                   title: "Border Widths"
                   width: panelWidth

                   ColumnLayout {
                       anchors.centerIn: parent

                       Repeater {
                           model: [
                               "borderWidthSmall",
                               "borderWidthMid",
                               "borderWidthBig"
                           ]

                           RowLayout {
                               spacing: QP.Theme.spacingMid

                               QP.Text {
                                   text: modelData + ": "
                                   horizontalAlignment: Text.AlignRight
                                   Layout.alignment: Qt.AlignRight
                                   Layout.preferredWidth: 150
                               }

                               QP.SpinBox {
                                   value: QP.Theme[modelData]
                                   minimumValue: 0
                                   maximumValue: 100
                                   onValueChanged: QP.Theme[modelData] = value
                               }

                               Item {
                                   Layout.preferredWidth: Math.max(QP.Theme.radiusMid * 2, parent.height)
                                   Layout.preferredHeight: Layout.preferredWidth
                                   clip: true
                                   Rectangle {
                                       width: parent.width + radius
                                       height: parent.height + radius
                                       anchors.bottom: parent.bottom
                                       anchors.left: parent.left
                                       color: "transparent"
                                       border.color: QP.Theme.borderColor
                                       border.width: QP.Theme[modelData]
                                       radius: QP.Theme.radiusMid
                                   }
                               }
                           }
                       }
                   }
               }
           }
       }

       Tab {
           title: "Animations"

           QP.Panel {
               title: "Animation Durations"

               ColumnLayout {
                   anchors.centerIn: parent

                   Repeater {
                       model: [
                           "durationShort",
                           "durationMid",
                           "durationLong"
                       ]

                       RowLayout {
                           spacing: QP.Theme.spacingMid

                           QP.Text {
                               text: modelData + ": "
                               horizontalAlignment: Text.AlignRight
                               Layout.alignment: Qt.AlignRight
                               Layout.preferredWidth: 150
                           }

                           QP.SpinBox {
                               value: QP.Theme[modelData]
                               suffix: " ms"
                               minimumValue: 0
                               maximumValue: 5000
                               onValueChanged: {
                                   QP.Theme[modelData] = value
                                   durationAnimation.restart()
                               }
                           }

                           Rectangle {
                               id: holder
                               color: QP.Theme.backgroundColor
                               radius: QP.Theme.radiusSmall
                               border.color: QP.Theme.borderColor
                               border.width: QP.Theme.borderWidthSmall
                               Layout.preferredWidth: 150
                               Layout.preferredHeight: parent.height

                               Rectangle {
                                   id: ball
                                   color: QP.Theme.highlightColor
                                   height: parent.height - 2 * parent.border.width
                                   width: height
                                   radius: height / 2
                                   anchors.verticalCenter: parent.verticalCenter

                                   Behavior on x {
                                       NumberAnimation {duration: QP.Theme[modelData]}
                                   }

                                   SequentialAnimation on x {
                                       id: durationAnimation
                                       NumberAnimation {to: holder.width - ball.height - 2 * holder.border.width; duration: QP.Theme[modelData]; easing.type: QP.Theme.defaultEasingType}
                                       PauseAnimation {duration: QP.Theme[modelData]}
                                       NumberAnimation {to: 0 + 2 * holder.border.width; duration: QP.Theme[modelData]; easing.type: QP.Theme.defaultEasingType}
                                       PauseAnimation {duration: QP.Theme[modelData]}
                                       loops: Animation.Infinite
                                   }
                               }
                           }
                       }
                   }
               }
           }
       }


    }
}

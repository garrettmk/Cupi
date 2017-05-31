pragma Singleton
import QtQuick 2.7
import Qt.labs.settings 1.0

QtObject {
    id: theme

    property color backgroundColor:         "#262123"
    property color backgroundColorMid:      Qt.lighter(backgroundColor, 1.1)
    property color backgroundColorLight:    Qt.lighter(backgroundColorMid, 3.0)

    property color borderColor:             Qt.lighter(backgroundColor, 2)
    property color borderColorDark:         Qt.lighter(backgroundColorMid, 1.5)

    property color highlightColor:      "#5c7aff"
    onHighlightColorChanged: {
        color1.to = Qt.rgba(highlightColor.r,
                            highlightColor.g,
                            highlightColor.b,
                            0.7)
        color2.to = highlightColor
        textSelectionAnimation.restart()
    }

    property color textColor:           "white"
    property color textSelectionColor:  highlightColor
    property color selectedTextColor:   textColor

    SequentialAnimation on textSelectionColor {
        id: textSelectionAnimation

        ColorAnimation {
            id: color1
            to: highlightColor
            duration: durationLong * 2
            easing.type: Easing.OutSine
        }
        ColorAnimation {
            id: color2
            to: Qt.rgba(highlightColor.r,
                        highlightColor.g,
                        highlightColor.b,
                        0.7)
            duration: durationLong * 2
            easing.type: Easing.OutSine
        }
        loops: Animation.Infinite
    }

    property int textPointSize:         12
    property int textPointSizeSmall:    Math.round(textPointSize * 0.75)
    property int textPointSizeMid:      Math.round(textPointSize * 1.2)
    property int textPointSizeBig:      Math.round(textPointSize * 1.5)

    property int spacingBig:            15
    property int spacingMid:            10
    property int spacingSmall:          5

    property int radiusSmall:           3
    property int radiusMid:             5
    property int radiusBig:             10

    property int borderWidthSmall:      1
    property int borderWidthMid:        2
    property int borderWidthBig:        4

    property int durationShort:         150
    property int durationMid:           250
    property int durationLong:          500

    property int defaultEasingType:     Easing.InOutCubic
    property int fadeEasingType:        Easing.OutQuad

    property int toolButtonSizeSmall:   16
    property int toolButtonSizeMid:     32

    // Helper functions
    function borderWithAlpha(alpha) {
        return Qt.rgba(borderColor.r, borderColor.g, borderColor.b, alpha)
    }

    // Automatic settings
    property Settings settings: Settings {
        category: "Cupi"

        property alias backgroundColor: theme.backgroundColor
        property alias backgroundColorMid: theme.backgroundColorMid
        property alias backgroundColorLight: theme.backgroundColorLight
        property alias borderColor: theme.borderColor
        property alias borderColorDark: theme.borderColorDark

        property alias highlightColor: theme.highlightColor
        property alias textColor: theme.textColor
        property alias selectedTextColor: theme.selectedTextColor

        property alias textPointSize: theme.textPointSize
        property alias textPointSizeSmall: theme.textPointSizeSmall
        property alias textPointSizeMid: theme.textPointSizeMid
        property alias textPointSizeBig: theme.textPointSizeBig

        property alias spacingSmall: theme.spacingSmall
        property alias spacingMid: theme.spacingMid
        property alias spacingBig: theme.spacingBig

        property alias radiusSmall: theme.radiusSmall
        property alias radiusMid: theme.radiusMid
        property alias radiusBig: theme.radiusBig

        property alias borderWidthSmall: theme.borderWidthSmall
        property alias borderWidthMid: theme.borderWidthMid
        property alias borderWidthBig: theme.borderWidthBig

        property alias durationShort: theme.durationShort
        property alias durationMid: theme.durationMid
        property alias durationLong: theme.durationLong

        property alias defaultEasingType: theme.defaultEasingType
        property alias fadeEasingType: theme.fadeEasingType

        property alias toolButtonSizeSmall: theme.toolButtonSizeSmall
        property alias toolButtonSizeMid: theme.toolButtonSizeMid
    }
}

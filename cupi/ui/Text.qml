import QtQuick 2.7
import "." as Themed

Text {
    color:          Themed.Theme.textColor
    elide:          Text.ElideRight
    textFormat:     Text.PlainText
    font.pointSize: Themed.Theme.textPointSize
}

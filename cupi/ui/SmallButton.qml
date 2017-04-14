import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

Button {
    id: root
    property bool bold: false

    style: Themed.ButtonStyle {
        id: style
        borderAlpha: control.hovered ? 1 : 0
        fontPointSize: Themed.Theme.textPointSizeSmall
        fontBold: root.bold
        defaultWidth: 30
        defaultHeight: 15
        radius: Themed.Theme.radiusSmall
    }
}

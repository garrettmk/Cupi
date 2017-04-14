import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as Themed

Button {
    id: root
    property bool bold: false

    style: Themed.ButtonStyle {
        fontBold: root.bold
    }
}

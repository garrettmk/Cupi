import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import "." as QP

Button {
    id: root
    implicitWidth: QP.Theme.toolButtonSizeSmall + 4
    implicitHeight: QP.Theme.toolButtonSizeSmall + 4
    property bool bold: false

    style: QP.ButtonStyle {
        borderAlpha: control.hovered ? 1 : 0
        fontPointSize: QP.Theme.textPointSizeSmall
        fontBold: root.bold
        radius: QP.Theme.radiusSmall
    }
}

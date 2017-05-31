import QtQuick 2.7
import "." as QP

QP.SmallToolButton {
    property bool folded: false
    iconSource: folded ? "icons/arrow-down.png" : "icons/arrow-up.png"
}

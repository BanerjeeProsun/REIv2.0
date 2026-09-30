import QtQuick
import QtQuick.Controls
import ".."

// Minimal overlay scrollbar: a thin translucent pill that widens on hover.
ScrollBar {
    id: bar
    policy: ScrollBar.AsNeeded
    padding: 2
    background: null
    contentItem: Rectangle {
        implicitWidth: bar.hovered || bar.pressed ? 8 : 5
        radius: width / 2
        color: bar.pressed ? Theme.hairlineStrong : Qt.rgba(1, 1, 1, bar.hovered ? 0.18 : 0.10)
        opacity: bar.active || bar.hovered ? 1 : 0
        Behavior on implicitWidth { NumberAnimation { duration: Theme.fast } }
        Behavior on opacity { NumberAnimation { duration: 240 } }
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }
}

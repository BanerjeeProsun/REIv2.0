import QtQuick
import QtQuick.Controls
import ".."

// Small dark tooltip: graphite chip, 1px keyline, 12px Porcelain label.
ToolTip {
    id: tip
    delay: 500
    padding: 0
    topPadding: 5
    bottomPadding: 5
    leftPadding: 10
    rightPadding: 10
    contentItem: ReiText {
        role: "utilityNav"
        text: tip.text
        color: Theme.porcelain
    }
    background: Rectangle {
        color: Theme.graphite
        radius: Theme.radiusLink
        border.width: 1
        border.color: Theme.steel
    }
    enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.fast } }
    exit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.exit } }
}

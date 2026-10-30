import QtQuick
import ".."

// Keyboard focus outline from DESIGN.md: 1px Apple Blue with a 1px offset.
// Place inside a control; it follows the parent's shape.
Rectangle {
    property bool shown: parent ? parent.activeFocus : false
    property real baseRadius: parent && parent.radius !== undefined ? parent.radius : height / 2
    anchors.fill: parent
    anchors.margins: -2
    radius: baseRadius + 2
    color: "transparent"
    border.width: 1
    border.color: Theme.appleBlue
    visible: shown
    z: 10
}

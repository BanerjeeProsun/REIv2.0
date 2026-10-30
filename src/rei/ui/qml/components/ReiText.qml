import QtQuick
import ".."

// Text set in one of the DESIGN.md type roles (Theme.type), so family, size,
// weight, tracking and line height never drift between screens.
Text {
    property string role: "body"
    readonly property var spec: Theme.type[role] || Theme.type["body"]

    color: Theme.porcelain
    font.family: spec.display ? Theme.fontDisplay : Theme.fontText
    font.pixelSize: spec.size
    font.weight: spec.weight
    font.letterSpacing: spec.tracking
    lineHeight: spec.lh
    textFormat: Text.PlainText
    Behavior on color { ColorAnimation { duration: Theme.fast } }
}

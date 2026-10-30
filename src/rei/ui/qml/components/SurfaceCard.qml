import QtQuick
import QtQuick.Layouts
import ".."

// Carbon panel on the black stage: 28px corners, no shadow (DESIGN.md).
// Hoverable cards pick up a Steel keyline instead of lifting.
// Height always follows its content, so text can never spill outside the card.
Rectangle {
    id: root
    default property alias content: body.data
    property int padding: Theme.cardPadding
    property bool hoverable: false
    property bool outlined: false
    readonly property bool hovered: hover.hovered

    Layout.fillWidth: true
    implicitHeight: body.implicitHeight + padding * 2
    radius: Theme.radiusCard
    color: hoverable && hovered ? Theme.carbonHover : Theme.carbon
    border.width: outlined || (hoverable && hovered) ? 1 : 0
    border.color: Theme.steel
    Behavior on color { ColorAnimation { duration: Theme.fast } }

    HoverHandler { id: hover; enabled: root.hoverable }

    ColumnLayout {
        id: body
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: root.padding
        spacing: Theme.s12
    }
}

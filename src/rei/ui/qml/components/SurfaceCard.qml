import QtQuick
import QtQuick.Layouts
import ".."

// Elevated Plum card: 20px radius, 24px padding, no border (surface colour separates it).
// Height always follows its content, so text can never spill outside the card.
Rectangle {
    id: root
    default property alias content: body.data
    property int padding: Theme.cardPadding
    property bool hoverable: false
    readonly property bool hovered: hover.hovered

    Layout.fillWidth: true
    implicitHeight: body.implicitHeight + padding * 2
    radius: Theme.radiusCard
    color: hoverable && hovered ? Theme.elevatedHover : Theme.elevated
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

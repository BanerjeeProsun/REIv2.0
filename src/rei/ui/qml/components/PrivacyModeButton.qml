import QtQuick
import QtQuick.Layouts
import ".."

// Current privacy mode as an Outlined Explore Pill in the utility bar.
// Clicking never switches the mode: it opens the confirmation dialog.
Item {
    id: root
    property bool compact: false
    readonly property string mode: backend.privacyModeText || "Local Only"
    readonly property bool hovered: mouse.containsMouse

    implicitHeight: 28
    implicitWidth: row.implicitWidth + 2 * Theme.s12
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: "Privacy mode: " + root.mode

    Rectangle {
        id: shape
        anchors.fill: parent
        radius: height / 2
        color: root.hovered ? Theme.hoverFill : "transparent"
        border.width: 1
        border.color: root.hovered ? Theme.porcelain : Theme.slate
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Behavior on border.color { ColorAnimation { duration: Theme.fast } }
    }
    FocusRing { shown: root.activeFocus; baseRadius: shape.radius }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: Theme.s6
        Icon {
            Layout.alignment: Qt.AlignVCenter
            source: PrivacyModes.icon(PrivacyModes.indexOf(root.mode))
            size: 13
            color: Theme.porcelain
        }
        ReiText {
            visible: !root.compact
            Layout.alignment: Qt.AlignVCenter
            role: "utilityNav"
            text: root.mode
            color: Theme.porcelain
        }
    }

    ReiToolTip {
        visible: mouse.containsMouse
        text: root.compact ? root.mode + " · Change privacy mode" : "Change privacy mode"
    }

    function open() { backend.requestPrivacyMode("") }
    Keys.onReturnPressed: open()
    Keys.onEnterPressed: open()
    Keys.onSpacePressed: open()

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.open()
    }
}

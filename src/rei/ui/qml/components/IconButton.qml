import QtQuick
import ".."

// Round compact control (send, stop, player). variant: "primary" (Apple Blue),
// "capsule" (translucent graphite) or "ghost" (bare glyph, fill on hover).
Item {
    id: root
    property url iconSource
    property string variant: "ghost"
    property int size: 36
    property int iconSize: Math.round(size * 0.42)
    property string tooltip: ""
    property real iconOffsetX: 0
    signal clicked()

    readonly property bool hovered: mouse.containsMouse && root.enabled
    readonly property bool pressed: mouse.pressed && root.enabled

    implicitWidth: size
    implicitHeight: size
    activeFocusOnTab: root.enabled
    opacity: root.enabled ? 1 : 0.4
    Accessible.role: Accessible.Button
    Accessible.name: root.tooltip

    Rectangle {
        id: shape
        anchors.fill: parent
        radius: width / 2
        color: root.variant === "primary" ? (root.pressed ? Theme.appleBluePressed : root.hovered ? Theme.appleBlueHover : Theme.appleBlue)
             : root.variant === "capsule" ? (root.hovered ? Theme.capsuleHover : Theme.capsule)
             : (root.hovered ? Theme.hoverFill : "transparent")
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }
    FocusRing { shown: root.activeFocus; baseRadius: shape.radius }

    Icon {
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: root.iconOffsetX
        source: root.iconSource
        size: root.iconSize
        color: root.variant === "primary" ? Theme.white
             : root.hovered || root.variant === "capsule" ? Theme.porcelain : Theme.navInk
    }

    scale: root.pressed ? 0.96 : 1
    Behavior on scale { NumberAnimation { duration: Theme.exit; easing.type: Easing.OutCubic } }

    ReiToolTip {
        visible: root.tooltip !== "" && mouse.containsMouse
        text: root.tooltip
    }

    Keys.onReturnPressed: if (root.enabled) root.clicked()
    Keys.onEnterPressed: if (root.enabled) root.clicked()
    Keys.onSpacePressed: if (root.enabled) root.clicked()

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (root.enabled) root.clicked()
    }
}

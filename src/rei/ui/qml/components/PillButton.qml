import QtQuick
import QtQuick.Layouts
import ".."

// Pill button (DESIGN.md: buttons are fully round, never rectangular).
// variant: "primary"  - Apple Blue fill, the one primary action in a group
//          "outline"  - Outlined Explore Pill: 1px Slate, Porcelain text
//          "capsule"  - Dark Pricing Capsule: translucent graphite fill
//          "ghost"    - text-only Electric Link
Item {
    id: root
    property string text: ""
    property url iconSource
    property string variant: "outline"
    property bool small: false
    signal clicked()

    readonly property bool hasIcon: iconSource.toString() !== ""
    readonly property bool hovered: mouse.containsMouse && root.enabled
    readonly property bool pressed: mouse.pressed && root.enabled

    implicitHeight: small ? 30 : 38
    implicitWidth: row.implicitWidth + (small ? 28 : 36)
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight
    activeFocusOnTab: root.enabled
    opacity: root.enabled ? 1 : 0.4
    Behavior on opacity { NumberAnimation { duration: Theme.fast } }

    readonly property color fill: {
        if (variant === "primary") return pressed ? Theme.appleBluePressed : hovered ? Theme.appleBlueHover : Theme.appleBlue
        if (variant === "capsule") return hovered ? Theme.capsuleHover : Theme.capsule
        if (variant === "outline") return hovered ? Theme.hoverFill : "transparent"
        return "transparent"
    }
    readonly property color ink: variant === "primary" ? Theme.white
                               : variant === "ghost" ? Theme.electricLink
                               : variant === "capsule" ? (hovered ? Theme.porcelain : Theme.navInk)
                               : Theme.porcelain

    Rectangle {
        id: shape
        anchors.fill: parent
        radius: height / 2
        color: root.fill
        border.width: root.variant === "outline" ? 1 : 0
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
            visible: root.hasIcon
            source: root.iconSource
            size: root.small ? 13 : 15
            Layout.alignment: Qt.AlignVCenter
            color: root.ink
        }
        ReiText {
            visible: root.text !== ""
            Layout.alignment: Qt.AlignVCenter
            role: root.small ? "utilityNav" : "body"
            text: root.text
            color: root.ink
            font.weight: root.variant === "primary" || root.variant === "outline" ? 500 : 400
            font.underline: root.variant === "ghost" && root.hovered
        }
    }

    scale: root.pressed ? 0.97 : 1
    Behavior on scale { NumberAnimation { duration: Theme.exit; easing.type: Easing.OutCubic } }

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

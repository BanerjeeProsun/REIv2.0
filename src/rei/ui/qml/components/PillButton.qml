import QtQuick
import QtQuick.Layouts
import ".."

// Pill button. variant: "primary" (coral CTA), "outline", "ghost".
Item {
    id: root
    property string text: ""
    property url iconSource
    property string variant: "outline"
    property bool small: false
    signal clicked()

    readonly property bool hasIcon: iconSource.toString() !== ""
    readonly property bool hovered: mouse.containsMouse && root.enabled

    implicitHeight: small ? 32 : 40
    implicitWidth: row.implicitWidth + (small ? 28 : 40)
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight
    activeFocusOnTab: root.enabled

    readonly property color fill: {
        if (!root.enabled) return variant === "primary" ? Theme.elevated : "transparent"
        if (variant === "primary") return mouse.pressed ? Theme.coralPressed : hovered ? Theme.coralHover : Theme.coral
        if (variant === "outline") return hovered ? Theme.elevated : "transparent"
        return hovered ? Theme.elevated : "transparent"
    }
    readonly property color ink: !root.enabled ? Theme.textMuted
                               : variant === "primary" ? Theme.textPrimary
                               : hovered ? Theme.textPrimary : Theme.textBody

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: root.fill
        border.width: root.variant === "outline" || root.activeFocus ? 1 : 0
        border.color: root.activeFocus ? Theme.coralAlpha(0.7)
                    : root.hovered ? Theme.hairlineStrong : Theme.hairline
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Behavior on border.color { ColorAnimation { duration: Theme.fast } }
    }

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 8
        Icon {
            visible: root.hasIcon
            source: root.iconSource
            size: root.small ? 14 : 16
            Layout.alignment: Qt.AlignVCenter
            color: root.ink
        }
        Text {
            visible: root.text !== ""
            Layout.alignment: Qt.AlignVCenter
            text: root.text
            color: root.ink
            font.family: Theme.fontText
            font.pixelSize: root.small ? 13 : Theme.sizeBodySm
            font.weight: Font.DemiBold
            font.letterSpacing: Theme.tracking(Theme.sizeBodySm) / 2
            Behavior on color { ColorAnimation { duration: Theme.fast } }
        }
    }

    scale: mouse.pressed && root.enabled ? 0.96 : 1
    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

    Keys.onReturnPressed: if (root.enabled) root.clicked()
    Keys.onSpacePressed: if (root.enabled) root.clicked()

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: if (root.enabled) root.clicked()
    }
}

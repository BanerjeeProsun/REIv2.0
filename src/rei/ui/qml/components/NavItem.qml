import QtQuick
import QtQuick.Layouts
import ".."

// Sidebar navigation row: icon + label on one vertical axis, coral accent bar when active.
Item {
    id: root
    property string text: ""
    property url iconSource
    property bool active: false
    property string shortcutHint: ""
    signal clicked()

    implicitHeight: 40
    Layout.fillWidth: true

    readonly property bool hovered: mouse.containsMouse

    Rectangle {
        id: bg
        anchors.fill: parent
        radius: Theme.radiusControl
        color: root.active ? Theme.elevated
             : root.hovered ? Qt.rgba(38 / 255, 37 / 255, 59 / 255, 0.55)
             : "transparent"
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }

    // Active indicator: grows from the centre when the item becomes active
    Rectangle {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        width: 3
        height: root.active ? 18 : 0
        radius: 1.5
        color: Theme.coral
        opacity: root.active ? 1 : 0
        Behavior on height { NumberAnimation { duration: Theme.page; easing.type: Easing.OutCubic } }
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 12
        spacing: 12

        Icon {
            source: root.iconSource
            size: 18
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
            Layout.alignment: Qt.AlignVCenter
            color: root.active ? Theme.textPrimary : root.hovered ? Theme.textBody : Theme.textSecondary
        }

        Text {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            text: root.text
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            color: root.active ? Theme.textPrimary : root.hovered ? Theme.textBody : Theme.textSecondary
            font.family: Theme.fontText
            font.pixelSize: Theme.sizeBodySm
            font.weight: root.active ? Font.DemiBold : Font.Medium
            font.letterSpacing: Theme.tracking(Theme.sizeBodySm) / 2
            Behavior on color { ColorAnimation { duration: Theme.fast } }
        }

        Text {
            visible: root.shortcutHint !== ""
            Layout.alignment: Qt.AlignVCenter
            text: root.shortcutHint
            color: Theme.textMuted
            opacity: root.hovered || root.active ? 1 : 0
            font.family: Theme.fontText
            font.pixelSize: Theme.sizeCaption
            Behavior on opacity { NumberAnimation { duration: Theme.fast } }
        }
    }

    scale: mouse.pressed ? 0.98 : 1
    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}

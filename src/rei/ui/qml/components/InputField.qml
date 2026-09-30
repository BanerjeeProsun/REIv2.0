import QtQuick
import QtQuick.Layouts
import ".."

// Labelled text field (8px radius) with an animated coral focus ring.
ColumnLayout {
    id: root
    property string label: ""
    property string placeholder: ""
    property alias text: field.text
    property alias input: field
    signal accepted()

    Layout.fillWidth: true
    spacing: Theme.s8

    Text {
        visible: root.label !== ""
        text: root.label
        color: field.activeFocus ? Theme.textPrimary : Theme.textSecondary
        font.family: Theme.fontText
        font.pixelSize: Theme.sizeBodySm
        font.weight: Font.Medium
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }

    Rectangle {
        Layout.fillWidth: true
        implicitHeight: 52
        radius: Theme.radiusInput + 4
        color: field.activeFocus ? Theme.elevatedHover : hover.hovered ? Qt.darker(Theme.elevatedHover, 1.06) : Theme.elevated
        border.width: 1
        border.color: field.activeFocus ? Theme.coralAlpha(0.65) : "transparent"
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Behavior on border.color { ColorAnimation { duration: Theme.fast } }

        HoverHandler { id: hover; cursorShape: Qt.IBeamCursor }

        TextInput {
            id: field
            anchors.fill: parent
            anchors.leftMargin: Theme.s16
            anchors.rightMargin: Theme.s16
            verticalAlignment: TextInput.AlignVCenter
            color: Theme.textPrimary
            selectionColor: Theme.coralAlpha(0.45)
            selectedTextColor: Theme.textPrimary
            font.family: Theme.fontText
            font.pixelSize: Theme.sizeBody
            clip: true
            onAccepted: root.accepted()

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: root.placeholder
                color: Theme.textMuted
                visible: field.text.length === 0
                font: field.font
            }
        }
    }
}

import QtQuick
import QtQuick.Layouts
import ".."

// Labelled text field in the DESIGN.md Device Selector style: faint white fill,
// 1px Slate outline, fully round, Apple Blue focus outline.
ColumnLayout {
    id: root
    property string label: ""
    property string placeholder: ""
    property alias text: field.text
    property alias input: field
    property bool secret: false
    signal accepted()

    Layout.fillWidth: true
    spacing: Theme.s8

    ReiText {
        visible: root.label !== ""
        Layout.leftMargin: Theme.s4
        role: "bodyStrong"
        text: root.label
        color: field.activeFocus ? Theme.porcelain : Theme.ash
    }

    Rectangle {
        id: shape
        Layout.fillWidth: true
        implicitHeight: 48
        radius: height / 2
        color: hover.hovered && !field.activeFocus ? Theme.fieldFillHover : Theme.fieldFill
        border.width: 1
        border.color: hover.hovered || field.activeFocus ? Theme.ash : Theme.slate
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Behavior on border.color { ColorAnimation { duration: Theme.fast } }

        HoverHandler { id: hover; cursorShape: Qt.IBeamCursor }
        TapHandler { onTapped: field.forceActiveFocus() }
        FocusRing { shown: field.activeFocus; baseRadius: shape.radius }

        TextInput {
            id: field
            anchors.fill: parent
            anchors.leftMargin: Theme.s24
            anchors.rightMargin: Theme.s24
            verticalAlignment: TextInput.AlignVCenter
            color: Theme.porcelain
            selectionColor: Theme.alpha(Theme.appleBlue, 0.55)
            selectedTextColor: Theme.white
            font.family: Theme.fontText
            font.pixelSize: Theme.type.reading.size
            font.letterSpacing: Theme.type.reading.tracking
            clip: true
            activeFocusOnTab: true
            echoMode: root.secret ? TextInput.Password : TextInput.Normal
            passwordCharacter: "•"
            onAccepted: root.accepted()

            ReiText {
                anchors.verticalCenter: parent.verticalCenter
                role: "reading"
                text: root.placeholder
                color: Theme.ash
                visible: field.text.length === 0
            }
        }
    }
}

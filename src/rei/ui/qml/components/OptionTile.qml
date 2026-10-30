import QtQuick
import QtQuick.Layouts
import ".."

// Selectable option row: a black tile with a Steel keyline inside a Carbon
// dialog. Selected = Apple Blue keyline and a check; never a coloured fill.
Rectangle {
    id: root
    property string title: ""
    property string description: ""
    property url iconSource
    property bool selected: false
    property string trailingLabel: ""
    signal clicked()

    readonly property bool hovered: mouse.containsMouse

    Layout.fillWidth: true
    implicitHeight: row.implicitHeight + 2 * Theme.s16
    radius: Theme.radiusNav
    color: root.hovered && !root.selected ? Theme.graphite : Theme.obsidian
    border.width: 1
    border.color: root.selected ? Theme.appleBlue : root.hovered ? Theme.slate : Theme.steel
    Behavior on color { ColorAnimation { duration: Theme.fast } }
    Behavior on border.color { ColorAnimation { duration: Theme.fast } }

    Accessible.role: Accessible.RadioButton
    Accessible.name: root.title
    Accessible.checked: root.selected

    RowLayout {
        id: row
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Theme.s16
        anchors.rightMargin: Theme.s16
        spacing: Theme.s14

        Icon {
            visible: root.iconSource.toString() !== ""
            Layout.alignment: Qt.AlignTop
            Layout.topMargin: 2
            source: root.iconSource
            size: 20
            color: root.selected ? Theme.porcelain : Theme.ash
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s8
                ReiText {
                    role: "sectionNav"
                    text: root.title
                    color: Theme.porcelain
                }
                ReiText {
                    visible: root.trailingLabel !== ""
                    Layout.alignment: Qt.AlignVCenter
                    role: "utilityNav"
                    text: root.trailingLabel
                    color: Theme.ash
                }
                Item { Layout.fillWidth: true }
            }
            ReiText {
                Layout.fillWidth: true
                visible: root.description !== ""
                role: "body"
                text: root.description
                color: Theme.ash
                wrapMode: Text.WordWrap
            }
        }

        // Selection mark
        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
            radius: 10
            color: root.selected ? Theme.appleBlue : "transparent"
            border.width: root.selected ? 0 : 1
            border.color: Theme.slate
            Behavior on color { ColorAnimation { duration: Theme.fast } }
            Icon {
                anchors.centerIn: parent
                source: Qt.resolvedUrl("../icons/check.svg")
                size: 12
                color: Theme.white
                opacity: root.selected ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: Theme.fast } }
            }
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}

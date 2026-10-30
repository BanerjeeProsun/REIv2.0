import QtQuick
import QtQuick.Layouts
import ".."

// Card row: black icon tile, title + description, trailing control.
// The text column fills the space between icon and control and wraps, so it
// can never overflow the card.
SurfaceCard {
    id: root
    property string title: ""
    property string description: ""
    property url iconSource
    // Children given by users of SettingRow become the trailing controls
    default property alias trailing: trailingRow.data

    padding: Theme.s20

    content: RowLayout {
        Layout.fillWidth: true
        spacing: Theme.s16

        Rectangle {
            visible: root.iconSource.toString() !== ""
            Layout.preferredWidth: 40
            Layout.preferredHeight: 40
            Layout.alignment: Qt.AlignVCenter
            radius: Theme.radiusLink + 2
            color: Theme.obsidian
            border.width: 1
            border.color: Theme.steel
            Icon {
                anchors.centerIn: parent
                source: root.iconSource
                size: 18
                color: Theme.porcelain
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 2
            ReiText {
                Layout.fillWidth: true
                role: "sectionNav"
                text: root.title
                elide: Text.ElideRight
            }
            ReiText {
                visible: root.description !== ""
                Layout.fillWidth: true
                role: "body"
                text: root.description
                color: Theme.ash
                wrapMode: Text.WordWrap
            }
        }

        RowLayout {
            id: trailingRow
            Layout.alignment: Qt.AlignVCenter
            spacing: Theme.s8
        }
    }
}

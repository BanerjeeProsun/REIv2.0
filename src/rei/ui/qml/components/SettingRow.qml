import QtQuick
import QtQuick.Layouts
import ".."

// Card row: icon tile, title + description, trailing control.
// The text column fills the space between icon and control and wraps, so it
// can never overflow the card.
SurfaceCard {
    id: root
    property string title: ""
    property string description: ""
    property url iconSource
    // Children given by users of SettingRow become the trailing controls
    default property alias trailing: trailingRow.data

    content: RowLayout {
        Layout.fillWidth: true
        spacing: Theme.s16

        Rectangle {
            visible: root.iconSource.toString() !== ""
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            Layout.alignment: Qt.AlignVCenter
            radius: 12
            color: Qt.rgba(1, 1, 1, 0.05)
            Icon {
                anchors.centerIn: parent
                source: root.iconSource
                size: 20
                color: Theme.textBody
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 4
            Text {
                Layout.fillWidth: true
                text: root.title
                color: Theme.textPrimary
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBody
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Text {
                visible: root.description !== ""
                Layout.fillWidth: true
                text: root.description
                color: Theme.textSecondary
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBodySm
                lineHeight: 1.3
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

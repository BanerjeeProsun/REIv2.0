import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    id: page
    title: "Memory"
    subtitle: "What Rei remembers about you, encrypted on this device."

    // Called by Main.qml whenever this page becomes visible
    function activated() { if (typeof memoryModel !== "undefined") memoryModel.refresh() }

    actions: PillButton {
        text: "Refresh"
        iconSource: Qt.resolvedUrl("../icons/refresh.svg")
        small: true
        onClicked: page.activated()
    }

    // Empty state
    SurfaceCard {
        visible: memoryRepeater.count === 0
        padding: 40
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8
            Icon {
                Layout.alignment: Qt.AlignHCenter
                source: Qt.resolvedUrl("../icons/memory.svg")
                size: 28
                color: Theme.textMuted
            }
            Text {
                Layout.fillWidth: true
                Layout.topMargin: 8
                horizontalAlignment: Text.AlignHCenter
                text: "No memories yet"
                color: Theme.textPrimary
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.sizeSubheading
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: "Ask Rei to remember something and it will appear here."
                color: Theme.textSecondary
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBodySm
                wrapMode: Text.WordWrap
            }
        }
    }

    Repeater {
        id: memoryRepeater
        model: typeof memoryModel !== "undefined" ? memoryModel : 0
        SurfaceCard {
            hoverable: true
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s8
                Tag { text: model.kind }
                Tag { text: model.dataClass; ink: Theme.textMuted }
                Item { Layout.fillWidth: true }
                Text {
                    Layout.alignment: Qt.AlignVCenter
                    text: model.createdAt
                    color: Theme.textMuted
                    font.family: Theme.fontText
                    font.pixelSize: Theme.sizeCaption
                }
            }
            Text {
                Layout.fillWidth: true
                text: model.content
                color: Theme.textBody
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBody
                lineHeight: 1.4
                wrapMode: Text.Wrap
            }
        }
    }
}

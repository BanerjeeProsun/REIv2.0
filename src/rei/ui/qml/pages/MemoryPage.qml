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

    EmptyState {
        visible: memoryRepeater.count === 0
        iconSource: Qt.resolvedUrl("../icons/memory.svg")
        title: "No memories yet"
        body: "Ask Rei to remember something and it will appear here."
    }

    Repeater {
        id: memoryRepeater
        model: typeof memoryModel !== "undefined" ? memoryModel : 0
        SurfaceCard {
            hoverable: true
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s8
                Tag { text: model.kind; ink: Theme.porcelain }
                Tag { text: model.dataClass }
                Item { Layout.fillWidth: true }
                ReiText {
                    Layout.alignment: Qt.AlignVCenter
                    role: "utilityNav"
                    text: model.createdAt
                    color: Theme.ash
                }
            }
            ReiText {
                Layout.fillWidth: true
                role: "reading"
                text: model.content
                wrapMode: Text.Wrap
            }
        }
    }
}

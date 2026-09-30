import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    id: page
    title: "Capabilities"
    subtitle: "Everything Rei can do on this device, and how much trust each action needs."

    function tierLabel(tier) {
        return tier === "R0" ? "Read only"
             : tier === "R1" ? "Low risk"
             : tier === "R2" ? "Asks first"
             : tier === "R3" ? "Needs review"
             : "Restricted"
    }

    // Two columns when there is room, one when the window is narrow
    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 900 ? 2 : 1
        columnSpacing: Theme.s16
        rowSpacing: Theme.s16

        Repeater {
            model: typeof capabilityModel !== "undefined" ? capabilityModel : 0
            SurfaceCard {
                hoverable: true
                Layout.fillWidth: true
                Layout.preferredWidth: 1   // equal column widths
                Layout.fillHeight: true

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.s8
                    Text {
                        Layout.fillWidth: true
                        text: model.summary
                        color: Theme.textPrimary
                        font.family: Theme.fontText
                        font.pixelSize: Theme.sizeBody
                        font.weight: Font.DemiBold
                        wrapMode: Text.WordWrap
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: model.id
                    color: Theme.textMuted
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.sizeCaption
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    spacing: Theme.s8
                    Tag {
                        text: page.tierLabel(model.tier)
                        dot: true
                        // Coral is reserved for the few high-risk actions
                        dotColor: model.tier === "R3" || model.tier === "R4" ? Theme.coral : Theme.textSecondary
                    }
                    Tag { text: model.network ? "Uses network" : "On-device" }
                    Item { Layout.fillWidth: true }
                }
            }
        }
    }
}

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

    // Feature tiles: two columns when there is room, one when narrow
    GridLayout {
        Layout.fillWidth: true
        columns: page.width > 900 ? 2 : 1
        columnSpacing: Theme.s12
        rowSpacing: Theme.s12

        Repeater {
            model: typeof capabilityModel !== "undefined" ? capabilityModel : 0
            SurfaceCard {
                hoverable: true
                Layout.fillWidth: true
                Layout.preferredWidth: 1   // equal column widths
                Layout.fillHeight: true

                ReiText {
                    Layout.fillWidth: true
                    role: "productLabel"
                    text: model.summary
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    text: model.id
                    color: Theme.ash
                    font.family: Theme.fontMono
                    font.pixelSize: Theme.type.utilityNav.size
                    elide: Text.ElideRight
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Theme.s4
                    spacing: Theme.s8
                    Tag {
                        text: page.tierLabel(model.tier)
                        dot: true
                        // Red is reserved for the few high-risk actions
                        dotColor: model.tier === "R3" || model.tier === "R4" ? Theme.alert : Theme.ash
                    }
                    Tag { text: model.network ? "Uses network" : "On-device" }
                    Item { Layout.fillWidth: true }
                }
            }
        }
    }
}

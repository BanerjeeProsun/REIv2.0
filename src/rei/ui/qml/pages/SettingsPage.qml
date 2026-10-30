import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    id: page
    title: "Settings"
    subtitle: "Control what Rei can see, where it thinks, and how it sounds."

    readonly property int modeIndex: PrivacyModes.indexOf(backend.privacyModeText)

    SectionLabel { text: "Privacy" }

    SettingRow {
        title: PrivacyModes.names[page.modeIndex]
        description: PrivacyModes.descriptions[page.modeIndex]
        iconSource: PrivacyModes.icon(page.modeIndex)

        // Shows the current mode; picking another asks for confirmation first
        SegmentedControl {
            options: PrivacyModes.shortNames
            segmentWidth: 104
            currentIndex: page.modeIndex
            onSelected: (index) => backend.requestPrivacyMode(PrivacyModes.names[index])
        }
    }

    SectionLabel { text: "Voice" }

    SettingRow {
        title: "Speech recognition"
        description: "Whisper (base), English, running on-device. Background noise is filtered out, and you can say “stop” to interrupt Rei."
        iconSource: Qt.resolvedUrl("../icons/mic.svg")
        Tag {
            text: backend.state === "idle" ? "Mic off" : "Mic live"
            dot: true
            dotColor: backend.state === "idle" ? Theme.ash : Theme.porcelain
        }
    }

    SettingRow {
        title: "Voice output"
        description: "Kokoro neural voice, synthesised locally. Press Esc or tap the orb to stop it mid-sentence."
        iconSource: Qt.resolvedUrl("../icons/chat.svg")
        Tag { text: "On-device" }
    }

    SectionLabel { text: "Models" }

    SettingRow {
        title: "LLM backend"
        description: "Dynamic model unloading and hardware acceleration settings."
        iconSource: Qt.resolvedUrl("../icons/capabilities.svg")
        // Release-status marker: text only, never a badge (DESIGN.md)
        ReiText { role: "caption"; text: "Coming soon"; color: Theme.copperNew }
    }
}

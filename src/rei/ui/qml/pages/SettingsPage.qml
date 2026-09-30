import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    id: page
    title: "Settings"
    subtitle: "Control what Rei can see, where it thinks, and how it sounds."

    readonly property var modes: ["Local Only", "Local + Connectors", "Cloud Assisted"]
    readonly property int modeIndex: Math.max(0, modes.indexOf(backend.privacyModeText))
    readonly property var descriptions: [
        "Everything runs on this device. Nothing you say or type leaves your computer.",
        "Rei still thinks on-device, but services you connect (email, music) can go online.",
        "Complex requests use the cloud planner. Names, emails and secrets are replaced on-device before anything is sent."
    ]

    SectionLabel { text: "Privacy" }

    SettingRow {
        title: page.modes[page.modeIndex]
        description: page.descriptions[page.modeIndex]
        iconSource: Qt.resolvedUrl(["../icons/local.svg", "../icons/connectors.svg", "../icons/cloud.svg"][page.modeIndex])

        SegmentedControl {
            options: ["Local", "+ Connectors", "Cloud"]
            segmentWidth: 104
            currentIndex: page.modeIndex
            onSelected: (index) => backend.setPrivacyMode(page.modes[index])
        }
    }

    SectionLabel { text: "Voice" }

    SettingRow {
        title: "Speech recognition"
        description: "Whisper (base), English, running on-device."
        iconSource: Qt.resolvedUrl("../icons/mic.svg")
        Tag { text: backend.state === "idle" ? "Mic off" : "Mic live"; dot: true; dotColor: backend.state === "idle" ? Theme.textMuted : Theme.coral }
    }

    SettingRow {
        title: "Voice output"
        description: "Kokoro neural voice, synthesised locally."
        iconSource: Qt.resolvedUrl("../icons/chat.svg")
        Tag { text: "On-device" }
    }

    SectionLabel { text: "Models" }

    SettingRow {
        title: "LLM backend"
        description: "Dynamic model unloading and hardware acceleration settings."
        iconSource: Qt.resolvedUrl("../icons/capabilities.svg")
        Tag { text: "Coming soon" }
    }
}

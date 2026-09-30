import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    id: page
    title: "Settings"
    subtitle: "Control what Rei can see, where it thinks, and how it sounds."

    readonly property bool cloud: backend.privacyModeText === "Cloud Assisted"

    SectionLabel { text: "Privacy" }

    SettingRow {
        title: page.cloud ? "Cloud Assisted" : "Local Only"
        description: page.cloud
            ? "Complex requests use the cloud planner. Names, emails and secrets are replaced on-device before anything is sent."
            : "Everything runs on this device. Nothing you say or type leaves your computer."
        iconSource: Qt.resolvedUrl(page.cloud ? "../icons/cloud.svg" : "../icons/local.svg")

        SegmentedControl {
            options: ["Local only", "Cloud assisted"]
            currentIndex: page.cloud ? 1 : 0
            onSelected: backend.togglePrivacyMode()
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

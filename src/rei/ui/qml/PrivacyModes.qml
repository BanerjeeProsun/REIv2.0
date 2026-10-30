pragma Singleton
import QtQuick

// The three privacy modes, shared by the utility bar, Settings, Connectors and
// the confirmation dialog. Names must match ReiUI.PRIVACY_MODES / main.MODES.
QtObject {
    readonly property var names: ["Local Only", "Local + Connectors", "Cloud Assisted"]
    readonly property var shortNames: ["Local", "+ Connectors", "Cloud"]
    readonly property var descriptions: [
        "Everything runs on this device. Nothing you say or type leaves your computer.",
        "Rei still thinks on-device, but services you connect (email, music) can go online.",
        "Complex requests use the cloud planner. Names, emails and secrets are replaced on-device before anything is sent."
    ]
    readonly property var icons: ["icons/local.svg", "icons/connectors.svg", "icons/cloud.svg"]

    function indexOf(name) { return Math.max(0, names.indexOf(name)) }
    // Icon URL relative to the qml/ folder, for use from components/ or pages/
    function icon(index) { return Qt.resolvedUrl(icons[index]) }
}

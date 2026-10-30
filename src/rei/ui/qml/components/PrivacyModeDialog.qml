import QtQuick
import QtQuick.Layouts
import ".."

// Confirm a privacy-mode change. Nothing changes until "Switch to ..." is
// pressed: Cancel, Esc and clicking outside leave the mode as it was.
// Up/Down move the selection, Enter switches.
ReiDialog {
    id: root
    title: "Privacy mode"
    subtitle: "Choose where Rei thinks and what it can reach."
    preferredWidth: 540

    readonly property int currentIndex: PrivacyModes.indexOf(backend.privacyModeText)
    property int selectedIndex: 0
    readonly property bool changed: selectedIndex !== currentIndex
    readonly property bool cloudSelected: PrivacyModes.names[selectedIndex] === "Cloud Assisted"

    // mode: the requested mode to preselect, or "" for the current one
    function openFor(mode) {
        selectedIndex = mode ? PrivacyModes.indexOf(mode) : currentIndex
        open()
    }
    function move(step) {
        var n = PrivacyModes.names.length
        selectedIndex = (selectedIndex + step + n) % n
    }
    function confirm() {
        if (changed) backend.setPrivacyMode(PrivacyModes.names[selectedIndex])
        close()
    }
    function cancel() { close() }

    onOpened: options.forceActiveFocus()

    FocusScope {
        id: options
        Layout.fillWidth: true
        implicitHeight: list.implicitHeight
        activeFocusOnTab: true

        Keys.onUpPressed: root.move(-1)
        Keys.onDownPressed: root.move(1)
        Keys.onReturnPressed: root.confirm()
        Keys.onEnterPressed: root.confirm()

        ColumnLayout {
            id: list
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: Theme.s8

            Repeater {
                model: PrivacyModes.names.length
                OptionTile {
                    required property int index
                    title: PrivacyModes.names[index]
                    description: PrivacyModes.descriptions[index]
                    iconSource: PrivacyModes.icon(index)
                    selected: root.selectedIndex === index
                    trailingLabel: root.currentIndex === index ? "Current" : ""
                    onClicked: {
                        root.selectedIndex = index
                        options.forceActiveFocus()
                    }
                }
            }
        }
        // No separate focus ring: the selected tile's Apple Blue keyline is
        // where ↑/↓ and Enter act
    }

    // What changes when the cloud planner is allowed
    Rectangle {
        Layout.fillWidth: true
        visible: root.cloudSelected && root.changed
        implicitHeight: notice.implicitHeight + 2 * Theme.s14
        radius: Theme.radiusLink + 4
        color: Theme.obsidian
        border.width: 1
        border.color: Theme.steel

        RowLayout {
            id: notice
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: Theme.s14
            anchors.rightMargin: Theme.s14
            spacing: Theme.s12
            Icon {
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 1
                source: Qt.resolvedUrl("../icons/cloud.svg")
                size: 16
                color: Theme.porcelain
            }
            ReiText {
                Layout.fillWidth: true
                role: "body"
                text: "Complex requests may be sent to the cloud planner. Names, emails and secrets are anonymised on-device first."
                color: Theme.porcelain
                wrapMode: Text.WordWrap
            }
        }
    }

    buttons: [
        PillButton {
            text: "Cancel"
            variant: "outline"
            onClicked: root.cancel()
        },
        PillButton {
            objectName: "privacySwitchButton"
            text: root.changed ? "Switch to " + PrivacyModes.names[root.selectedIndex] : "Switch"
            variant: "primary"
            enabled: root.changed
            onClicked: root.confirm()
        }
    ]
}

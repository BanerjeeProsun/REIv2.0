import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: window
    visible: true
    width: 1180
    height: 780
    minimumWidth: 880
    minimumHeight: 600
    title: "Rei"
    color: Theme.obsidian

    property int currentPage: 0
    // Open ReiDialogs (maintained by ReiDialog). While > 0, Esc belongs to the dialog.
    property int dialogDepth: 0
    readonly property bool interruptible: backend.state === "processing" || backend.state === "speaking"

    readonly property var pages: [
        { name: "Chat",         source: "pages/HomePage.qml" },
        { name: "Activity",     source: "pages/ActivityPage.qml" },
        { name: "Memory",       source: "pages/MemoryPage.qml" },
        { name: "Capabilities", source: "pages/CapabilitiesPage.qml" },
        { name: "Connectors",   source: "pages/ConnectorsPage.qml" },
        { name: "Settings",     source: "pages/SettingsPage.qml" }
    ]

    // Ctrl+1..6 jumps between pages
    Instantiator {
        model: window.pages.length
        delegate: Shortcut {
            sequence: "Ctrl+" + (index + 1)
            onActivated: window.currentPage = index
        }
    }

    // Esc stops Rei mid-thought or mid-sentence, unless a dialog is open
    // (then Esc is the dialog's: cancel / deny).
    Shortcut {
        sequence: "Esc"
        context: Qt.WindowShortcut
        enabled: window.interruptible && window.dialogDepth === 0 && !backend.needsSetup
        onActivated: backend.interrupt()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TopBar {
            Layout.fillWidth: true
            pages: window.pages
            currentPage: window.currentPage
            onPageSelected: (index) => window.currentPage = index
        }

        // PAGES: all pages stay alive (chat history, scroll positions survive),
        // the active one glides up and fades in; the old one fades out quickly.
        Item {
            id: pageHost
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            Repeater {
                model: window.pages
                Loader {
                    id: pageLoader
                    required property int index
                    required property var modelData
                    readonly property bool current: window.currentPage === index
                    width: pageHost.width
                    height: pageHost.height
                    source: modelData.source
                    asynchronous: false
                    z: current ? 1 : 0
                    enabled: current
                    // Pages may define activated() to refresh when shown (e.g. Memory)
                    onCurrentChanged: if (current && item && typeof item.activated === "function") item.activated()
                    visible: opacity > 0.001
                    opacity: current ? 1 : 0
                    Behavior on opacity {
                        NumberAnimation { duration: pageLoader.current ? Theme.page : Theme.exit; easing.type: Easing.OutCubic }
                    }
                    transform: Translate {
                        y: pageLoader.current ? 0 : 12
                        Behavior on y { NumberAnimation { duration: Theme.page; easing.type: Easing.OutCubic } }
                    }
                }
            }
        }
    }

    // ONBOARDING: a black stage with the orb as the object on display
    Rectangle {
        id: setupOverlay
        anchors.fill: parent
        color: Theme.obsidian
        z: 100
        opacity: backend.needsSetup ? 1 : 0
        visible: opacity > 0.001
        Behavior on opacity { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }

        // Swallow clicks so nothing underneath reacts while setup is shown
        MouseArea { anchors.fill: parent; hoverEnabled: true }

        readonly property bool ready: nameField.text.trim() !== "" && purposeField.text.trim() !== ""
        function submit() {
            if (ready) backend.completeOnboarding(nameField.text.trim(), purposeField.text.trim())
        }

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(520, parent.width - 80)
            spacing: Theme.s32

            VoiceOrb {
                Layout.alignment: Qt.AlignHCenter
                size: 120
                st: "idle"
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                ReiText {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    role: "display"
                    text: "Hello, I'm Rei."
                }
                ReiText {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    role: "display"
                    text: "Let's get acquainted."
                    color: Theme.ash
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Theme.s20
                InputField {
                    id: nameField
                    label: "What should I call you?"
                    placeholder: "Your name"
                    onAccepted: purposeField.input.forceActiveFocus()
                    Component.onCompleted: if (backend.needsSetup) input.forceActiveFocus()
                }
                InputField {
                    id: purposeField
                    label: "What will you mostly use me for?"
                    placeholder: "e.g. research, writing, staying organised"
                    onAccepted: setupOverlay.submit()
                }
            }

            PillButton {
                Layout.alignment: Qt.AlignHCenter
                text: "Initialize"
                variant: "primary"
                enabled: setupOverlay.ready
                onClicked: setupOverlay.submit()
            }
        }
    }

    // CONFIRMATION (voice or click). Esc answers "no".
    ReiDialog {
        id: confirmDialog
        title: "Confirmation required"
        escClosable: false

        property string intentId: ""
        property string message: ""
        property string hint: ""
        property int seconds: 0
        property bool strict: false
        property real remaining: 1.0
        NumberAnimation on remaining { id: countdownAnim; running: false; from: 1.0; to: 0.0 }

        function answer(approved) {
            backend.sendConfirmationResponse(intentId, approved)
            close()
        }
        onClosed: { countdownAnim.stop(); hint = ""; seconds = 0 }

        ReiText {
            Layout.fillWidth: true
            role: "reading"
            text: confirmDialog.message
            color: Theme.porcelain
            wrapMode: Text.Wrap
        }

        // Voice answer hint: pulsing mic + what to say
        RowLayout {
            Layout.fillWidth: true
            visible: confirmDialog.hint !== ""
            spacing: Theme.s10
            Rectangle {
                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                Layout.alignment: Qt.AlignVCenter
                radius: 14
                color: Theme.capsule
                Icon {
                    anchors.centerIn: parent
                    source: Qt.resolvedUrl("icons/mic.svg")
                    size: 14
                    color: Theme.porcelain
                }
                SequentialAnimation on opacity {
                    running: confirmDialog.opened && confirmDialog.hint !== ""
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.45; duration: 650; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 1.0; duration: 650; easing.type: Easing.InOutSine }
                }
            }
            ReiText {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                role: "bodyStrong"
                text: confirmDialog.hint
                wrapMode: Text.WordWrap
            }
        }

        // Time left to answer
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 3
            radius: 1.5
            color: Theme.steel
            visible: confirmDialog.seconds > 0
            Rectangle {
                height: parent.height
                radius: 1.5
                color: confirmDialog.strict ? Theme.alert : Theme.porcelain
                width: parent.width * confirmDialog.remaining
            }
        }

        buttons: [
            PillButton { text: "Deny"; variant: "outline"; onClicked: confirmDialog.answer(false) },
            PillButton {
                text: confirmDialog.strict ? "Confirm" : "Allow"
                variant: "primary"
                onClicked: confirmDialog.answer(true)
            }
        ]
    }

    Shortcut {
        sequence: "Esc"
        enabled: confirmDialog.opened
        onActivated: confirmDialog.answer(false)
    }

    // PRIVACY MODE (opened from the utility bar, Settings or Connectors)
    PrivacyModeDialog {
        id: modeDialog
        objectName: "privacyModeDialog"
    }

    Connections {
        target: backend
        function onConfirmationRequested(title, msg, intent_id) {
            confirmDialog.title = title
            confirmDialog.message = msg
            confirmDialog.intentId = intent_id
            confirmDialog.hint = ""
            confirmDialog.seconds = 0
            confirmDialog.open()
        }
        function onConfirmationHint(hint, seconds, strict) {
            confirmDialog.hint = hint
            confirmDialog.strict = strict
            confirmDialog.seconds = seconds
            countdownAnim.duration = seconds * 1000
            countdownAnim.restart()
        }
        function onConfirmationClosed(intent_id) {
            // Answered by voice or timed out: close without sending a response
            if (confirmDialog.opened && confirmDialog.intentId === intent_id) confirmDialog.close()
        }
        function onPrivacyModeChangeRequested(mode) {
            modeDialog.openFor(mode)
        }
    }
}

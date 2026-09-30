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
    color: Theme.canvas

    property int currentPage: 0

    readonly property var pages: [
        { name: "Chat",         icon: "icons/chat.svg",         source: "pages/HomePage.qml" },
        { name: "Activity",     icon: "icons/activity.svg",     source: "pages/ActivityPage.qml" },
        { name: "Memory",       icon: "icons/memory.svg",       source: "pages/MemoryPage.qml" },
        { name: "Capabilities", icon: "icons/capabilities.svg", source: "pages/CapabilitiesPage.qml" },
        { name: "Connectors",   icon: "icons/connectors.svg",   source: "pages/ConnectorsPage.qml" },
        { name: "Settings",     icon: "icons/settings.svg",     source: "pages/SettingsPage.qml" }
    ]

    // Ctrl+1..5 jumps between pages
    Instantiator {
        model: window.pages.length
        delegate: Shortcut {
            sequence: "Ctrl+" + (index + 1)
            onActivated: window.currentPage = index
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // SIDEBAR
        Rectangle {
            Layout.preferredWidth: Theme.sidebarWidth
            Layout.fillHeight: true
            color: Theme.recessed

            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: 28
                anchors.bottomMargin: 20
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 4

                // Brand: aligned to the same 16px inset as the nav icons
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 16
                    Layout.bottomMargin: 28
                    spacing: 12
                    Rectangle {
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                        Layout.alignment: Qt.AlignVCenter
                        radius: 9
                        color: "transparent"
                        border.color: Theme.coral
                        border.width: 2
                        Rectangle {
                            anchors.centerIn: parent
                            width: 6; height: 6; radius: 3
                            color: Theme.coral
                            opacity: backend.state === "listening" || backend.state === "speaking" ? 1 : 0.35
                            Behavior on opacity { NumberAnimation { duration: Theme.page } }
                        }
                    }
                    Text {
                        Layout.alignment: Qt.AlignVCenter
                        text: "Rei"
                        color: Theme.textPrimary
                        font.family: Theme.fontDisplay
                        font.pixelSize: 20
                        font.weight: Font.DemiBold
                        font.letterSpacing: Theme.tracking(20)
                    }
                }

                Repeater {
                    model: window.pages
                    NavItem {
                        text: modelData.name
                        iconSource: Qt.resolvedUrl(modelData.icon)
                        active: window.currentPage === index
                        shortcutHint: "Ctrl " + (index + 1)
                        onClicked: window.currentPage = index
                    }
                }

                Item { Layout.fillHeight: true }

                // Privacy mode switch, pinned to the bottom of the rail
                Rectangle {
                    id: privacyChip
                    Layout.fillWidth: true
                    implicitHeight: 56
                    radius: Theme.radiusControl + 4
                    color: privacyMouse.containsMouse ? Theme.elevated : Qt.rgba(38 / 255, 37 / 255, 59 / 255, 0.5)
                    Behavior on color { ColorAnimation { duration: Theme.fast } }
                    readonly property string mode: backend.privacyModeText || "Local Only"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 12
                        Icon {
                            Layout.alignment: Qt.AlignVCenter
                            source: Qt.resolvedUrl(privacyChip.mode === "Cloud Assisted" ? "icons/cloud.svg"
                                                 : privacyChip.mode === "Local + Connectors" ? "icons/connectors.svg"
                                                 : "icons/local.svg")
                            size: 18
                            color: Theme.textBody
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.alignment: Qt.AlignVCenter
                            spacing: 1
                            Text {
                                text: backend.privacyModeText || "Local Only"
                                color: Theme.textPrimary
                                font.family: Theme.fontText
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                            }
                            Text {
                                text: privacyChip.mode === "Cloud Assisted" ? "Private data is anonymised"
                                    : privacyChip.mode === "Local + Connectors" ? "Approved services only"
                                    : "Nothing leaves this device"
                                color: Theme.textMuted
                                font.family: Theme.fontText
                                font.pixelSize: 11
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                    }
                    MouseArea {
                        id: privacyMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.togglePrivacyMode()
                    }
                }
            }

            // Hairline edge between rail and canvas
            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: Theme.hairline
            }
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

    // ONBOARDING / SETUP OVERLAY
    Rectangle {
        id: setupOverlay
        anchors.fill: parent
        color: Theme.canvas
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
            width: Math.min(480, parent.width - 80)
            spacing: 40

            VoiceOrb {
                Layout.alignment: Qt.AlignHCenter
                size: 120
                st: "idle"
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: "Hello, I'm Rei."
                    color: Theme.textPrimary
                    font.family: Theme.fontDisplay
                    font.pixelSize: 52
                    font.weight: Font.DemiBold
                    font.letterSpacing: Theme.tracking(52)
                }
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: "Let's get acquainted."
                    color: Theme.coral
                    font.family: Theme.fontDisplay
                    font.pixelSize: 52
                    font.weight: Font.DemiBold
                    font.letterSpacing: Theme.tracking(52)
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 20
                InputField {
                    id: nameField
                    label: "What should I call you?"
                    placeholder: "Your name"
                    onAccepted: purposeField.input.forceActiveFocus()
                    Component.onCompleted: input.forceActiveFocus()
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

    // CONFIRMATION DIALOG
    Popup {
        id: confirmDialog
        anchors.centerIn: parent
        width: Math.min(480, window.width - 80)
        padding: 28
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose

        property string intentId: ""
        function answer(approved) {
            backend.sendConfirmationResponse(intentId, approved)
            close()
        }

        Overlay.modal: Rectangle {
            color: Qt.rgba(8 / 255, 8 / 255, 14 / 255, 0.6)
            Behavior on opacity { NumberAnimation { duration: Theme.page } }
        }

        enter: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.page; easing.type: Easing.OutCubic }
                NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: Theme.page; easing.type: Easing.OutCubic }
            }
        }
        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.exit; easing.type: Easing.OutCubic }
        }

        background: Rectangle {
            color: Theme.elevated
            radius: Theme.radiusCard
            border.color: Theme.hairline
        }

        contentItem: ColumnLayout {
            spacing: 16

            Text {
                id: confirmTitle
                Layout.fillWidth: true
                text: "Confirmation required"
                color: Theme.textPrimary
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.sizeHeadingSm
                font.weight: Font.DemiBold
                font.letterSpacing: Theme.tracking(Theme.sizeHeadingSm)
                wrapMode: Text.WordWrap
            }

            Text {
                id: confirmMsg
                Layout.fillWidth: true
                text: ""
                color: Theme.textBody
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBodySm
                lineHeight: 1.4
                wrapMode: Text.Wrap
            }

            // Voice answer hint: pulsing mic + what to say
            RowLayout {
                Layout.fillWidth: true
                visible: confirmDialog.hint !== ""
                spacing: 10
                Rectangle {
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                    Layout.alignment: Qt.AlignVCenter
                    radius: 14
                    color: Theme.coralAlpha(0.16)
                    Icon {
                        anchors.centerIn: parent
                        source: Qt.resolvedUrl("icons/mic.svg")
                        size: 14
                        color: Theme.coral
                    }
                    SequentialAnimation on opacity {
                        running: confirmDialog.opened && confirmDialog.hint !== ""
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.45; duration: 650; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 650; easing.type: Easing.InOutSine }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    text: confirmDialog.hint
                    color: Theme.textPrimary
                    font.family: Theme.fontText
                    font.pixelSize: Theme.sizeBodySm
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
            }

            // Time left to answer
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 3
                radius: 1.5
                color: Qt.rgba(1, 1, 1, 0.06)
                visible: confirmDialog.seconds > 0
                Rectangle {
                    height: parent.height
                    radius: 1.5
                    color: confirmDialog.strict ? Theme.coral : Theme.textSecondary
                    width: parent.width * confirmDialog.remaining
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                spacing: 8
                Item { Layout.fillWidth: true }
                PillButton { text: "Deny"; variant: "ghost"; onClicked: confirmDialog.answer(false) }
                PillButton { text: confirmDialog.strict ? "Confirm" : "Allow"; variant: "primary"; onClicked: confirmDialog.answer(true) }
            }
        }

        property string hint: ""
        property int seconds: 0
        property bool strict: false
        property real remaining: 1.0
        NumberAnimation on remaining { id: countdownAnim; running: false; from: 1.0; to: 0.0 }
        onClosed: { countdownAnim.stop(); hint = ""; seconds = 0 }
    }

    Connections {
        target: backend
        function onConfirmationRequested(title, msg, intent_id) {
            confirmTitle.text = title
            confirmMsg.text = msg
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
    }
}

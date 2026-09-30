import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 1080
    height: 800
    title: "Rei"
    color: "#08090a" // Onyx Canvas
    
    // Theme Colors
    readonly property color colorOnyxCanvas: "#08090a"
    readonly property color colorCarbonSurface: "#141516"
    readonly property color colorGraphiteSurface: "#1c1c1f"
    readonly property color colorSmokeSurface: "#23252a"
    readonly property color colorIronSurface: "#2d2e31"
    readonly property color colorAshBorder: "#34343a"
    readonly property color colorFerriteBorder: "#3e3e44"
    readonly property color colorSteelText: "#62666d"
    readonly property color colorPewterText: "#7f7f80"
    readonly property color colorFogText: "#8a8f98"
    readonly property color colorMistText: "#d0d6e0"
    readonly property color colorChalkBorder: "#e4e5e9"
    readonly property color colorSnow: "#f7f8f8"

    // Typography
    readonly property string fontInter: "Inter Variable"
    readonly property string fontMono: "Berkeley Mono"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // TOP NAVIGATION BAR
        Rectangle {
            Layout.fillWidth: true
            height: 56
            color: colorOnyxCanvas
            
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: colorSmokeSurface
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                spacing: 24

                // Logo Area
                RowLayout {
                    spacing: 8
                    Rectangle {
                        width: 16; height: 16; radius: 8
                        color: "transparent"
                        border.color: colorSnow; border.width: 2
                    }
                    Text {
                        text: "Rei"
                        color: colorSnow
                        font.family: fontInter
                        font.pixelSize: 15
                        font.weight: 590
font.letterSpacing: -0.15
                    }
                }

                // Nav Links
                RowLayout {
                    spacing: 24
                    Layout.fillHeight: true
                    Repeater {
                        model: [
                            {name: "Chat", icon: "chat.svg"},
                            {name: "Activity", icon: "activity.svg"},
                            {name: "Memory", icon: "memory.svg"},
                            {name: "Capabilities", icon: "capabilities.svg"},
                            {name: "Settings", icon: "settings.svg"}
                        ]
                        RowLayout {
                            spacing: 8
                            Layout.alignment: Qt.AlignVCenter
                            
                            Image {
                                source: "icons/" + modelData.icon
                                sourceSize.width: 16
                                sourceSize.height: 16
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                // Use a simple ColorOverlay if available, but since we don't have it reliably:
                                // To make stroke colors right, we can load a raw SVG or use SVG color properties,
                                // but standard Image won't colorize easily. Actually, standard SVG strokes might just render black if not modified.
                                // Let's just assume we used currentColor, which in QML might default to black.
                                // We can use IconImage, but let's just keep the text colored.
                            }

                            Text {
                                text: modelData.name
                                color: stackView.currentIndex === index ? colorSnow : colorFogText
                                font.family: fontInter
                                font.pixelSize: 14
                                font.weight: 510
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: stackView.currentIndex = index
                            }
                        }
                    }
                }
                
                Item { Layout.fillWidth: true } // spacer
                
                // Status / Privacy Mode indicator
                Rectangle {
                    height: 28
                    width: privacyRow.width + 24
                    radius: 14
                    color: "transparent"
                    border.color: colorSmokeSurface
                    RowLayout {
                        id: privacyRow
                        anchors.centerIn: parent
                        spacing: 6
                        Image {
                            source: backend.privacyModeText === "Cloud Assisted" ? "icons/cloud.svg" : "icons/local.svg"
                            sourceSize.width: 14; sourceSize.height: 14
                            Layout.preferredWidth: 14; Layout.preferredHeight: 14
                        }
                        Text {
                            text: backend.privacyModeText || "Local Only"
                            color: colorFogText
                            font.family: fontInter
                            font.pixelSize: 13
                        }
                    }
                }
            }
        }

        // MAIN CONTENT STACK
        StackLayout {
            id: stackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: 0

            Loader { source: "pages/HomePage.qml" }
            Loader { source: "pages/ActivityPage.qml" }
            Loader { source: "pages/MemoryPage.qml" }
            Loader { source: "pages/CapabilitiesPage.qml" }
            Loader { source: "pages/SettingsPage.qml" }
        }
    }

    // ONBOARDING / SETUP OVERLAY
    Rectangle {
        id: setupOverlay
        anchors.fill: parent
        color: colorOnyxCanvas
        z: 100
        visible: backend.needsSetup
        opacity: visible ? 1.0 : 0.0
        Behavior on opacity { NumberAnimation { duration: 800; easing.type: Easing.InOutQuad } }

        ColumnLayout {
            anchors.centerIn: parent
            width: 440
            spacing: 48

            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 16
                Text {
                    text: "Rei"
                    color: colorSnow
                    font.family: fontInter
                    font.pixelSize: 48
                    font.weight: 590
                    font.letterSpacing: -1.056
                    Layout.alignment: Qt.AlignHCenter
                }
                Text {
                    text: "Initialization Sequence"
                    color: colorMistText
                    font.family: fontInter
                    font.pixelSize: 16
                    font.letterSpacing: -0.15
                    Layout.alignment: Qt.AlignHCenter
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 24

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text { text: "What should I call you?"; color: colorFogText; font.family: fontInter; font.pixelSize: 14 }
                    Rectangle {
                        Layout.fillWidth: true; height: 48; radius: 4
                        color: colorCarbonSurface
                        border.color: nameInput.activeFocus ? colorSnow : colorAshBorder
                        border.width: 1
                        Behavior on border.color { ColorAnimation { duration: 200 } }
                        TextInput {
                            id: nameInput
                            anchors.fill: parent; anchors.margins: 16
                            color: colorSnow; font.family: fontInter; font.pixelSize: 16
                            verticalAlignment: TextInput.AlignVCenter
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Text { text: "What is your primary focus?"; color: colorFogText; font.family: fontInter; font.pixelSize: 14 }
                    Rectangle {
                        Layout.fillWidth: true; height: 48; radius: 4
                        color: colorCarbonSurface
                        border.color: purposeInput.activeFocus ? colorSnow : colorAshBorder
                        border.width: 1
                        Behavior on border.color { ColorAnimation { duration: 200 } }
                        TextInput {
                            id: purposeInput
                            anchors.fill: parent; anchors.margins: 16
                            color: colorSnow; font.family: fontInter; font.pixelSize: 16
                            verticalAlignment: TextInput.AlignVCenter
                        }
                    }
                }
            }

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                width: 140; height: 44; radius: 22
                color: "transparent"; border.color: (nameInput.text.trim() && purposeInput.text.trim()) ? colorSnow : colorAshBorder; border.width: 1
                Behavior on border.color { ColorAnimation { duration: 200 } }
                Text { 
                    text: "Initialize"; 
                    color: (nameInput.text.trim() && purposeInput.text.trim()) ? colorSnow : colorFogText; 
                    anchors.centerIn: parent; font.family: fontInter; font.pixelSize: 15; font.weight: 510 
                    Behavior on color { ColorAnimation { duration: 200 } }
                }
                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (nameInput.text.trim() !== "" && purposeInput.text.trim() !== "") {
                            backend.completeOnboarding(nameInput.text, purposeInput.text)
                        }
                    }
                }
            }
        }
    }

    // CONFIRMATION DIALOG OVERLAY
    Popup {
        id: confirmDialog
        anchors.centerIn: parent
        width: 480
        height: 280
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose
        
        property string intentId: ""

        background: Rectangle {
            color: colorCarbonSurface
            border.color: colorAshBorder
            border.width: 1
            radius: 8
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16

            Text {
                id: confirmTitle
                text: "Confirmation Required"
                color: colorSnow
                font.family: fontInter
                font.pixelSize: 24
                font.weight: 510
font.letterSpacing: -0.288
            }

            Text {
                id: confirmMsg
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: ""
                color: colorMistText
                font.family: fontInter
                font.pixelSize: 15
                lineHeight: 1.5
                wrapMode: Text.Wrap
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 12

                // Deny Button - Ghost
                Rectangle {
                    width: 80; height: 32; radius: 16
                    color: "transparent"
                    Text { 
                        text: "Deny"; color: colorFogText; anchors.centerIn: parent
                        font.family: fontInter; font.pixelSize: 14; font.weight: 510 
                    }
                    MouseArea {
                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                        onClicked: { backend.sendConfirmationResponse(confirmDialog.intentId, false); confirmDialog.close() }
                    }
                }

                // Allow Button - Outlined Pill
                Rectangle {
                    width: 80; height: 32; radius: 16
                    color: "transparent"; border.color: colorSnow; border.width: 1
                    Text { 
                        text: "Allow"; color: colorSnow; anchors.centerIn: parent
                        font.family: fontInter; font.pixelSize: 14; font.weight: 510 
                    }
                    MouseArea {
                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                        onClicked: { backend.sendConfirmationResponse(confirmDialog.intentId, true); confirmDialog.close() }
                    }
                }
            }
        }
    }

    Connections {
        target: backend
        function onConfirmationRequested(title, msg, intent_id) {
            confirmTitle.text = title
            confirmMsg.text = msg
            confirmDialog.intentId = intent_id
            confirmDialog.open()
        }
    }
}

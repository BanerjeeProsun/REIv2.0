import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    readonly property color colorCarbonSurface: "#141516"
    readonly property color colorAshBorder: "#34343a"
    readonly property color colorSteelText: "#62666d"
    readonly property color colorMistText: "#d0d6e0"
    readonly property color colorSnow: "#f7f8f8"
    readonly property color colorFogText: "#8a8f98"
    readonly property string fontInter: "Inter Variable"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 48
        spacing: 24

        Text {
            text: "Settings"
            color: colorSnow
            font.family: fontInter
            font.pixelSize: 32
            font.weight: 510
font.letterSpacing: -0.416
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: colorAshBorder }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 32

                // PRIVACY MODE SECTION
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    Text { text: "Privacy Mode"; color: colorSnow; font.family: fontInter; font.pixelSize: 15; font.weight: 510 }
                    
                    Rectangle {
                        Layout.fillWidth: true; height: 80; radius: 8
                        color: colorCarbonSurface; border.color: colorAshBorder
                        
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 16; spacing: 16
                            
                            Image {
                                source: backend.privacyModeText === "Cloud Assisted" ? "../icons/cloud.svg" : "../icons/local.svg"
                                sourceSize.width: 24; sourceSize.height: 24
                                Layout.preferredWidth: 24; Layout.preferredHeight: 24
                            }

                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 4
                                Text { text: backend.privacyModeText; color: colorSnow; font.family: fontInter; font.pixelSize: 15 }
                                Text { text: "Active privacy boundary routing policy."; color: colorMistText; font.family: fontInter; font.pixelSize: 14 }
                            }

                            Rectangle {
                                width: 80; height: 32; radius: 16
                                color: "transparent"; border.color: colorAshBorder; border.width: 1
                                Text { text: "Switch"; color: colorSnow; anchors.centerIn: parent; font.family: fontInter; font.pixelSize: 13; font.weight: 510 }
                                MouseArea {
                                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: backend.togglePrivacyMode()
                                }
                            }
                        }
                    }
                }

                // MODELS SECTION (Coming Soon)
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    Text { text: "Models Configuration"; color: colorSnow; font.family: fontInter; font.pixelSize: 15; font.weight: 510 }
                    
                    Rectangle {
                        Layout.fillWidth: true; height: 80; radius: 8
                        color: colorCarbonSurface; border.color: colorAshBorder
                        
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 16; spacing: 16
                            
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 4
                                Text { text: "LLM Backend"; color: colorSnow; font.family: fontInter; font.pixelSize: 15 }
                                Text { text: "Dynamic model unloading and hardware acceleration settings."; color: colorMistText; font.family: fontInter; font.pixelSize: 14 }
                            }

                            Rectangle {
                                width: 100; height: 28; radius: 14
                                color: "transparent"; border.color: colorAshBorder
                                Text { text: "Coming Soon"; color: colorSteelText; anchors.centerIn: parent; font.family: fontInter; font.pixelSize: 12 }
                            }
                        }
                    }
                }
            }
        }
    }
}

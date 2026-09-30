import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    readonly property color colorCarbonSurface: "#141516"
    readonly property color colorGraphiteSurface: "#1c1c1f"
    readonly property color colorAshBorder: "#34343a"
    readonly property color colorSteelText: "#62666d"
    readonly property color colorMistText: "#d0d6e0"
    readonly property color colorSnow: "#f7f8f8"
    readonly property color colorFogText: "#8a8f98"
    readonly property string fontInter: "Inter Variable"
    readonly property string fontMono: "Berkeley Mono"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 48
        spacing: 24

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "Capabilities Registry"
                color: colorSnow
                font.family: fontInter
                font.pixelSize: 32
                font.weight: 510
font.letterSpacing: -0.416
            }
        }

        Rectangle {
            Layout.fillWidth: true; height: 1; color: colorAshBorder
        }

        ListView {
            id: capList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: capabilityModel
            spacing: 8
            clip: true
            
            delegate: Rectangle {
                width: capList.width
                height: 72
                radius: 4
                color: "transparent"
                border.color: colorAshBorder
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 16

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: id
                            color: colorSnow
                            font.family: fontMono
                            font.pixelSize: 15
                        }
                        Text {
                            text: summary
                            color: colorMistText
                            font.family: fontInter
                            font.pixelSize: 14
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }

                    // TIER BADGE
                    Rectangle {
                        width: 40; height: 24; radius: 4
                        color: colorGraphiteSurface
                        border.color: colorAshBorder
                        Text { text: tier; color: colorFogText; anchors.centerIn: parent; font.family: fontInter; font.pixelSize: 12; font.weight: 510 }
                    }

                    // NETWORK BADGE
                    Rectangle {
                        width: 60; height: 24; radius: 4
                        color: colorGraphiteSurface
                        border.color: colorAshBorder
                        Text { text: network ? "Network" : "Local"; color: network ? colorMistText : colorFogText; anchors.centerIn: parent; font.family: fontInter; font.pixelSize: 12 }
                    }
                    
                    // TOGGLE (Coming Soon)
                    Rectangle {
                        width: 80; height: 24; radius: 12
                        color: "transparent"; border.color: colorAshBorder
                        Text { text: "Coming Soon"; color: colorSteelText; anchors.centerIn: parent; font.family: fontInter; font.pixelSize: 11 }
                    }
                }
            }
        }
    }
}

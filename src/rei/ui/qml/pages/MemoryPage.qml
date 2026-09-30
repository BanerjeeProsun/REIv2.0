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
    readonly property string fontMono: "Berkeley Mono"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 48
        spacing: 24

        // PAGE HEADER
        RowLayout {
            Layout.fillWidth: true
            
            Text {
                text: "Memory Ledger"
                color: colorSnow
                font.family: fontInter
                font.pixelSize: 32
                font.weight: 510
font.letterSpacing: -0.416
            }
            
            Item { Layout.fillWidth: true }
            
            // Sync / Refresh
            Rectangle {
                width: 32; height: 32; radius: 16
                color: "transparent"
                border.color: colorAshBorder; border.width: 1
                Image {
                    source: "../icons/refresh.svg"
                    sourceSize.width: 14; sourceSize.height: 14
                    anchors.centerIn: parent
                }
                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: memoryModel.refresh()
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true; height: 1; color: colorAshBorder
        }

        // CONTENT
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: memoryModel.rowCount() === 0 ? 0 : 1

            // Empty State
            Item {
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    Text { text: "No memories yet."; color: colorMistText; font.family: fontInter; font.pixelSize: 15; Layout.alignment: Qt.AlignHCenter }
                    Text { text: "Rei builds context as you interact."; color: colorSteelText; font.family: fontInter; font.pixelSize: 14; Layout.alignment: Qt.AlignHCenter }
                }
            }

            // Memory List
            ListView {
                id: memoryList
                model: memoryModel
                spacing: 16
                clip: true
                
                delegate: Rectangle {
                    width: memoryList.width
                    height: contentCol.implicitHeight + 32
                    radius: 8
                    color: colorCarbonSurface
                    border.color: colorAshBorder
                    border.width: 1

                    ColumnLayout {
                        id: contentCol
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Rectangle {
                                width: 8; height: 8; radius: 4
                                color: dataClass === "C0" ? "#e4e5e9" : "#62666d"
                            }

                            Text {
                                text: kind
                                color: colorSnow
                                font.family: fontMono
                                font.pixelSize: 15
                                font.weight: 590
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Text {
                                text: createdAt
                                color: colorSteelText
                                font.family: fontInter
                                font.pixelSize: 13
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: content
                            color: colorMistText
                            font.family: fontInter
                            font.pixelSize: 15
                            lineHeight: 1.5
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }
    }
}

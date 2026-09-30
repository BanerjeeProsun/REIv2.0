import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    readonly property color colorMistText: "#d0d6e0"
    readonly property color colorSnow: "#f7f8f8"
    readonly property color colorFogText: "#8a8f98"
    readonly property color colorAshBorder: "#34343a"
    readonly property string fontInter: "Inter Variable"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 48
        spacing: 24

        Text {
            text: "Activity Ledger"
            color: colorSnow
            font.family: fontInter
            font.pixelSize: 32
            font.weight: 510
font.letterSpacing: -0.416
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: colorAshBorder }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12
                
                Text {
                    text: "Activity Ledger — Coming Soon"
                    color: colorMistText
                    font.family: fontInter
                    font.pixelSize: 15
                    font.weight: 510
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Text {
                    text: "The unified audit stream is planned for a future release."
                    color: colorFogText
                    font.family: fontInter
                    font.pixelSize: 14
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}

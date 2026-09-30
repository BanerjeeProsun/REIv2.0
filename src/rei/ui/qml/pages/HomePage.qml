import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    
    // Theme colors
    readonly property color colorCarbonSurface: "#141516"
    readonly property color colorAshBorder: "#34343a"
    readonly property color colorSteelText: "#62666d"
    readonly property color colorMistText: "#d0d6e0"
    readonly property color colorSnow: "#f7f8f8"
    readonly property color colorFogText: "#8a8f98"
    readonly property color colorGold: "#E5C07B"

    readonly property string fontInter: "Inter Variable"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 48
        spacing: 24

        // ORB / STATUS AREA
        // The orb is always animated: it breathes at rest, pulses while
        // thinking, and follows live amplitude (mic when listening, Rei's own
        // voice when speaking), with a synthetic pulse if no amplitude exists.
        Item {
            id: orb
            Layout.alignment: Qt.AlignHCenter
            width: 160
            height: 160

            readonly property string st: backend.state
            property real level: Math.max(st === "listening" ? backend.volume : 0, backend.outputLevel)
            Behavior on level { NumberAnimation { duration: 80 } }

            property real breath: 0
            SequentialAnimation on breath {
                loops: Animation.Infinite
                NumberAnimation { from: 0; to: 1; duration: 1600; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1; to: 0; duration: 1600; easing.type: Easing.InOutSine }
            }

            property real pulse: 0
            SequentialAnimation on pulse {
                running: orb.st === "speaking" || orb.st === "processing"
                loops: Animation.Infinite
                NumberAnimation { from: 0.0; to: 1.0; duration: 400; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 1.0; to: 0.4; duration: 300; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 0.4; to: 0.9; duration: 500; easing.type: Easing.InOutQuad }
                NumberAnimation { from: 0.9; to: 0.0; duration: 400; easing.type: Easing.InOutQuad }
            }

            readonly property real energy: st === "speaking" ? Math.max(level, pulse * 0.6)
                                         : st === "processing" ? pulse * 0.3
                                         : st === "listening" ? Math.max(level, 0.15 * breath)
                                         : 0.12 * breath

            // Outer glow
            Rectangle {
                anchors.centerIn: parent
                width: 100; height: 100
                radius: 50
                color: Qt.rgba(229/255, 192/255, 123/255, 0.05 + 0.22 * orb.energy)
                scale: 1.0 + 0.05 * orb.breath + 0.45 * orb.energy
                Behavior on scale { NumberAnimation { duration: 90 } }
            }

            // Inner glow
            Rectangle {
                anchors.centerIn: parent
                width: 100; height: 100
                radius: 50
                color: Qt.rgba(247/255, 248/255, 248/255, 0.04 + 0.14 * orb.energy)
                scale: 0.85 + 0.12 * orb.energy
                Behavior on scale { NumberAnimation { duration: 90 } }
            }

            // Base circle
            Rectangle {
                anchors.centerIn: parent
                width: 100; height: 100
                radius: 50
                color: "transparent"
                border.color: orb.st === "processing" ? Qt.rgba(247/255, 248/255, 248/255, 0.2) : colorSnow
                border.width: 1
                scale: 1.0 + 0.02 * orb.breath
            }

            // Listening Rings
            Repeater {
                model: orb.st === "listening" ? 2 : 0
                Rectangle {
                    anchors.centerIn: parent
                    width: 100; height: 100
                    radius: 50
                    color: "transparent"
                    border.color: colorSnow
                    border.width: 1
                    SequentialAnimation on scale { loops: Animation.Infinite; PauseAnimation { duration: index * 1000 } NumberAnimation { from: 1.0; to: 1.8; duration: 2000 } }
                    SequentialAnimation on opacity { loops: Animation.Infinite; PauseAnimation { duration: index * 1000 } NumberAnimation { from: 0.3; to: 0.0; duration: 2000 } }
                }
            }

            // Processing Arc
            Canvas {
                anchors.fill: parent
                visible: orb.st === "processing"
                onVisibleChanged: if (visible) requestPaint()
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.clearRect(0, 0, width, height);
                    ctx.beginPath();
                    ctx.arc(width/2, height/2, 50, 0, Math.PI * 0.7);
                    ctx.strokeStyle = colorSnow;
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                }
                RotationAnimation on rotation { from: 0; to: 360; duration: 1200; loops: Animation.Infinite; running: orb.st === "processing" }
            }
        }

        // Status Text
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: backend.status
            color: colorMistText
            font.family: fontInter
            font.pixelSize: 15
            font.weight: 400
        }

        // CHAT LIST
        ListModel { id: chatModel }
        Connections {
            target: backend
            function onMessageAdded(text, is_user) {
                chatModel.append({"msgText": text, "isUser": is_user})
            }
        }

        ListView {
            id: chatList
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: chatModel
            spacing: 16
            clip: true
            
            delegate: Item {
                width: chatList.width
                height: Math.max(msgContent.implicitHeight, 24)

                RowLayout {
                    anchors.fill: parent
                    spacing: 12

                    // Rei Avatar (Only show for Rei)
                    Item {
                        width: 24; height: 24
                        Layout.alignment: Qt.AlignTop
                        visible: !isUser
                        Rectangle {
                            width: 16; height: 16; radius: 8
                            anchors.centerIn: parent
                            color: "transparent"
                            border.color: colorSnow; border.width: 1
                        }
                    }

                    // User Avatar spacing
                    Item {
                        width: 24; height: 24
                        Layout.alignment: Qt.AlignTop
                        visible: isUser
                        Text {
                            anchors.centerIn: parent
                            text: "U"
                            color: colorFogText
                            font.family: fontInter; font.pixelSize: 12
                        }
                    }

                    Text {
                        id: msgContent
                        Layout.fillWidth: true
                        text: msgText
                        color: isUser ? colorMistText : colorSnow
                        font.family: fontInter
                        font.pixelSize: 15
                        font.weight: 400
                        lineHeight: 1.5
                        wrapMode: Text.WordWrap
                    }
                }
            }
            onCountChanged: Qt.callLater(() => chatList.positionViewAtEnd())
        }

        // INPUT FIELD
        Rectangle {
            Layout.fillWidth: true
            height: 48
            radius: 4
            color: colorCarbonSurface
            border.color: chatInput.activeFocus ? colorSnow : colorAshBorder
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 12

                Text { text: ">"; color: colorFogText; font.family: fontInter; font.pixelSize: 15 }

                TextInput {
                    id: chatInput
                    Layout.fillWidth: true
                    color: colorSnow
                    font.family: fontInter
                    font.pixelSize: 15
                    verticalAlignment: TextInput.AlignVCenter
                    clip: true
                    
                    onAccepted: {
                        if (text.trim().length > 0) {
                            backend.sendTextMessage(text)
                            text = ""
                        }
                    }
                    
                    Text {
                        text: "Talk or type..."
                        color: colorSteelText
                        visible: !parent.text && !parent.activeFocus
                        anchors.verticalCenter: parent.verticalCenter
                        font.family: fontInter
                        font.pixelSize: 15
                    }
                }

                Image {
                    source: "qrc:/icons/send.svg" // fallback
                    sourceSize.width: 16; sourceSize.height: 16
                    Layout.preferredWidth: 16; Layout.preferredHeight: 16
                    visible: chatInput.text.trim().length > 0
                    Component.onCompleted: source = "../icons/send.svg"
                    MouseArea {
                        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (chatInput.text.trim().length > 0) {
                                backend.sendTextMessage(chatInput.text)
                                chatInput.text = ""
                            }
                        }
                    }
                }
            }
        }
    }
}

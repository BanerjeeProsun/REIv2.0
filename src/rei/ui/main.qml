import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 900
    height: 650
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"

    // Custom properties
    readonly property color bgColor: "#0A0A0B"
    readonly property color borderColor: "#222222"
    readonly property color goldColor: "#E5C07B"
    readonly property color textGray: "#888888"
    readonly property color activeBg: "#1C1914"

    Rectangle {
        id: bgRect
        anchors.fill: parent
        color: bgColor
        radius: 12
        border.color: borderColor
        border.width: 1
        clip: true

        // Drag handle for the whole background
        MouseArea {
            anchors.fill: parent
            property point clickPos: "0,0"
            onPressed: (mouse) => { clickPos = Qt.point(mouse.x, mouse.y) }
            onPositionChanged: (mouse) => {
                mainWindow.x += mouse.x - clickPos.x
                mainWindow.y += mouse.y - clickPos.y
            }
        }

        // --- TOP HEADER ---
        Item {
            id: topHeader
            width: parent.width
            height: 60
            z: 10

            // Logo
            RowLayout {
                anchors.left: parent.left
                anchors.leftMargin: 25
                anchors.verticalCenter: parent.verticalCenter
                spacing: 10

                Rectangle {
                    width: 14; height: 14; radius: 7
                    color: "transparent"
                    border.color: goldColor
                    border.width: 2
                }
                Text {
                    text: "Rei"
                    color: "white"
                    font.pixelSize: 16
                    font.bold: true
                    font.family: "Segoe UI"
                }
            }

            // Window Controls
            RowLayout {
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 15

                Text { text: "—"; color: textGray; font.pixelSize: 12; font.bold: true; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: mainWindow.showMinimized() } }
                Text { text: "□"; color: textGray; font.pixelSize: 16; font.bold: true; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor } }
                Text { text: "✕"; color: textGray; font.pixelSize: 14; font.bold: true; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: Qt.quit() } }
            }
        }

        // --- SIDEBAR ---
        Item {
            id: sidebar
            width: 220
            anchors.top: topHeader.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left

            ColumnLayout {
                id: sideNav
                anchors.fill: parent
                anchors.topMargin: 10
                anchors.leftMargin: 15
                anchors.rightMargin: 15
                spacing: 5
                property int activeIndex: 0

                ListModel {
                    id: navModel
                    ListElement { name: "Chat"; icon: "💬" }
                    ListElement { name: "Activity"; icon: "⏱" }
                    ListElement { name: "Memory"; icon: "🧠" }
                    ListElement { name: "Capabilities"; icon: "⚡" }
                    ListElement { name: "Settings"; icon: "⚙" }
                }

                Repeater {
                    model: navModel
                    Rectangle {
                        Layout.fillWidth: true
                        height: 40
                        radius: 8
                        color: sideNav.activeIndex === index ? activeBg : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 15
                            spacing: 12
                            Text {
                                text: icon
                                color: sideNav.activeIndex === index ? goldColor : textGray
                                font.pixelSize: 14
                            }
                            Text {
                                text: name
                                color: sideNav.activeIndex === index ? goldColor : textGray
                                font.pixelSize: 14
                                font.family: "Segoe UI"
                                font.bold: sideNav.activeIndex === index
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onEntered: { if (sideNav.activeIndex !== index) parent.color = Qt.rgba(255,255,255,0.03) }
                            onExited: { if (sideNav.activeIndex !== index) parent.color = "transparent" }
                            onClicked: sideNav.activeIndex = index
                        }
                    }
                }
                Item { Layout.fillHeight: true }
            }
        }

        // --- MAIN CONTENT ---
        StackLayout {
            anchors.top: topHeader.bottom
            anchors.bottom: parent.bottom
            anchors.left: sidebar.right
            anchors.right: parent.right
            currentIndex: sideNav.activeIndex

            // Page 0: Chat
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 25
                    spacing: 20

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
                        spacing: 20
                        clip: true
                        delegate: Item {
                            width: chatList.width
                            height: isUser ? userBubble.height : reiMsg.height

                            // Rei Message (Left, no bubble, gold circle)
                            RowLayout {
                                id: reiMsg
                                visible: !isUser
                                width: parent.width * 0.8
                                spacing: 15
                                anchors.left: parent.left
                                Rectangle {
                                    Layout.alignment: Qt.AlignTop
                                    Layout.topMargin: 5
                                    width: 10; height: 10; radius: 5
                                    color: "transparent"
                                    border.color: goldColor; border.width: 1.5
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: msgText
                                    color: "white"
                                    font.pixelSize: 15
                                    font.family: "Segoe UI"
                                    wrapMode: Text.WordWrap
                                }
                            }

                            // User Message (Right, dark gray bubble)
                            Rectangle {
                                id: userBubble
                                visible: isUser
                                color: "#1A1A1A"
                                radius: 12
                                width: Math.min(userText.implicitWidth + 30, chatList.width * 0.7)
                                height: userText.implicitHeight + 24
                                anchors.right: parent.right
                                Text {
                                    id: userText
                                    text: msgText
                                    color: "white"
                                    anchors.centerIn: parent
                                    width: parent.width - 30
                                    wrapMode: Text.WordWrap
                                    font.pixelSize: 15
                                    font.family: "Segoe UI"
                                }
                            }
                        }
                        onCountChanged: Qt.callLater(() => chatList.positionViewAtEnd())
                    }

                    // Input Box (Pill)
                    Rectangle {
                        Layout.fillWidth: true
                        height: 50
                        radius: 25
                        color: "transparent"
                        border.color: "#333333"
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 15
                            anchors.rightMargin: 20
                            spacing: 15

                            // Plus icon
                            Rectangle {
                                width: 24; height: 24; radius: 12
                                color: "transparent"; border.color: textGray; border.width: 1
                                Text { text: "+"; color: textGray; anchors.centerIn: parent; font.pixelSize: 16 }
                            }

                            TextInput {
                                Layout.fillWidth: true
                                color: "white"
                                font.pixelSize: 15
                                font.family: "Segoe UI"
                                verticalAlignment: TextInput.AlignVCenter
                                clip: true
                                Text {
                                    text: "Talk or type..."
                                    color: textGray
                                    visible: !parent.text
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.family: "Segoe UI"
                                    font.pixelSize: 15
                                }
                            }

                            Text { text: "🎤"; color: textGray; font.pixelSize: 16 }
                        }
                    }
                }
            }

            // Page 1: Activity
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 30
                    spacing: 20
                    RowLayout {
                        Rectangle { width: 14; height: 14; radius: 7; color: "transparent"; border.color: goldColor; border.width: 2 }
                        Text { text: "Activity"; color: "white"; font.pixelSize: 20; font.bold: true; font.family: "Segoe UI" }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#0F0F10"
                        radius: 12
                        border.color: borderColor
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 25; spacing: 20
                            Text { text: "<font color='#E5C07B' face='monospace'>10:24</font> &nbsp;&nbsp; Opened Visual Studio Code"; color: "white"; font.pixelSize: 14 }
                            Text { text: "<font color='#E5C07B' face='monospace'>10:22</font> &nbsp;&nbsp; Read file: research_paper.pdf"; color: "white"; font.pixelSize: 14 }
                            Item { Layout.fillHeight: true }
                        }
                    }
                }
            }

            // Page 2: Memory
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 30
                    spacing: 20
                    RowLayout {
                        Rectangle { width: 14; height: 14; radius: 7; color: "transparent"; border.color: goldColor; border.width: 2 }
                        Text { text: "Memory"; color: "white"; font.pixelSize: 20; font.bold: true; font.family: "Segoe UI" }
                    }
                    Rectangle { Layout.fillWidth: true; height: 46; radius: 23; color: "transparent"; border.color: "#333333"
                        Text { text: "Search memories..."; color: textGray; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 20; font.family: "Segoe UI"; font.pixelSize: 14 }
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // Page 3: Capabilities
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 30
                    spacing: 20
                    RowLayout {
                        Rectangle { width: 14; height: 14; radius: 7; color: "transparent"; border.color: goldColor; border.width: 2 }
                        Text { text: "Capabilities"; color: "white"; font.pixelSize: 20; font.bold: true; font.family: "Segoe UI" }
                    }
                    RowLayout {
                        spacing: 20
                        Repeater {
                            model: ["All", "Applications", "Files", "Web", "System", "Devices"]
                            Text { text: modelData; color: index === 0 ? "white" : textGray; font.pixelSize: 14; font.bold: index===0 }
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        color: "#0F0F10"; radius: 12; border.color: borderColor
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 25; spacing: 20
                            RowLayout {
                                Text { text: "📂"; color: "white" }
                                Column {
                                    Text { text: "Filesystem"; color: "white"; font.pixelSize: 15; font.bold: true }
                                    Text { text: "Read, search, create, move, delete files."; color: textGray; font.pixelSize: 13 }
                                }
                                Item { Layout.fillWidth: true }
                                Rectangle { width: 80; height: 30; radius: 6; color: "transparent"; border.color: "#333333"; Text { text: "Allowed v"; color: "white"; anchors.centerIn: parent; font.pixelSize: 12 } }
                            }
                            Item { Layout.fillHeight: true }
                        }
                    }
                }
            }

            // Page 4: Settings
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 30
                    spacing: 20
                    RowLayout {
                        Rectangle { width: 14; height: 14; radius: 7; color: "transparent"; border.color: goldColor; border.width: 2 }
                        Text { text: "Settings"; color: "white"; font.pixelSize: 20; font.bold: true; font.family: "Segoe UI" }
                    }
                    RowLayout {
                        spacing: 25
                        Repeater {
                            model: ["General", "Voice", "Privacy", "Models", "Memory", "Appearance"]
                            Rectangle {
                                width: 70; height: 30; radius: 15
                                color: index === 0 ? "#1C1914" : "transparent"
                                Text { text: modelData; color: index === 0 ? goldColor : textGray; anchors.centerIn: parent; font.pixelSize: 13; font.bold: index===0 }
                            }
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        color: "#0F0F10"; radius: 12; border.color: borderColor
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 25; spacing: 20
                            Text { text: "Privacy Mode"; color: "white"; font.bold: true; font.pixelSize: 15 }
                            RadioButton { text: "Local Only"; checked: true; contentItem: Text { text: parent.text; color: "white"; leftPadding: 30 } }
                            RadioButton { text: "Cloud Assisted"; contentItem: Text { text: parent.text; color: "white"; leftPadding: 30 } }
                            Item { Layout.fillHeight: true }
                        }
                    }
                }
            }
        }
    }

    // --- COMPACT VOICE ORB (Window 14) ---
    Window {
        id: orbWindow
        visible: true
        width: 300; height: 400
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        color: "transparent"
        x: Screen.desktopAvailableWidth - width - 40
        y: 40

        Rectangle {
            anchors.fill: parent
            color: "#0A0A0B"
            radius: 16
            border.color: "#222222"
            border.width: 1

            MouseArea {
                anchors.fill: parent
                property point clickPos: "0,0"
                onPressed: (mouse) => { clickPos = Qt.point(mouse.x, mouse.y) }
                onPositionChanged: (mouse) => { orbWindow.x += mouse.x - clickPos.x; orbWindow.y += mouse.y - clickPos.y }
            }

            // Top header
            RowLayout {
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 20
                
                RowLayout {
                    spacing: 8
                    Rectangle { width: 12; height: 12; radius: 6; color: "transparent"; border.color: "#E5C07B"; border.width: 1.5 }
                    Text { text: "Rei"; color: "white"; font.pixelSize: 14; font.family: "Segoe UI" }
                }
                Item { Layout.fillWidth: true }
                Text { text: "⚙"; color: "#888888"; font.pixelSize: 16 }
            }

            // Central Orb
            Item {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -30
                width: 120; height: 120

                // Rings (Listening)
                Repeater {
                    model: backend.state === "listening" ? 3 : 0
                    Rectangle {
                        anchors.centerIn: parent
                        width: 100; height: 100
                        radius: 50
                        color: "transparent"
                        border.color: "#E5C07B"
                        border.width: 1
                        SequentialAnimation on scale { loops: Animation.Infinite; NumberAnimation { from: 1.0; to: 2.0; duration: 2000 } }
                        SequentialAnimation on opacity { loops: Animation.Infinite; NumberAnimation { from: 0.4; to: 0.0; duration: 2000 } }
                    }
                }

                // Processing Arc
                Canvas {
                    anchors.fill: parent
                    visible: backend.state === "processing"
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.clearRect(0, 0, width, height);
                        ctx.beginPath();
                        ctx.arc(width/2, height/2, 50, 0, Math.PI * 0.7);
                        ctx.strokeStyle = "#E5C07B";
                        ctx.lineWidth = 2;
                        ctx.stroke();
                    }
                    RotationAnimation on rotation { from: 0; to: 360; duration: 1000; loops: Animation.Infinite; running: backend.state === "processing" }
                }

                // Speaking Glow
                Rectangle {
                    anchors.centerIn: parent
                    width: 100 + (backend.volume * 80)
                    height: 100 + (backend.volume * 80)
                    radius: width/2
                    color: Qt.rgba(229/255, 192/255, 123/255, backend.volume * 0.4)
                    visible: backend.state === "speaking"
                    Behavior on width { NumberAnimation { duration: 100 } }
                    Behavior on height { NumberAnimation { duration: 100 } }
                }

                // Core Circle
                Rectangle {
                    anchors.centerIn: parent
                    width: 100; height: 100
                    radius: 50
                    color: "transparent"
                    border.color: backend.state === "processing" ? Qt.rgba(229/255, 192/255, 123/255, 0.2) : "#E5C07B"
                    border.width: 2
                }
            }

            // Status Text
            Text {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: 60
                text: backend.status
                color: "white"
                font.pixelSize: 16
                font.family: "Segoe UI"
            }

            // Waveform (Simulated during speaking)
            Row {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: 100
                spacing: 4
                visible: backend.state === "speaking"
                Repeater {
                    model: 10
                    Rectangle {
                        width: 3
                        height: 5 + (Math.random() * backend.volume * 30)
                        radius: 1.5
                        color: "#E5C07B"
                        anchors.verticalCenter: parent.verticalCenter
                        Timer {
                            interval: 100; running: backend.state === "speaking"; repeat: true
                            onTriggered: parent.height = 5 + (Math.random() * backend.volume * 30)
                        }
                        Behavior on height { NumberAnimation { duration: 100 } }
                    }
                }
            }

            // Cancel Button
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 25
                anchors.horizontalCenter: parent.horizontalCenter
                width: 120; height: 36
                radius: 18
                color: "#1A1A1A"
                border.color: "#333333"
                RowLayout {
                    anchors.centerIn: parent
                    spacing: 8
                    Text { text: "✕"; color: "white"; font.pixelSize: 12 }
                    Text { text: "Cancel"; color: "white"; font.pixelSize: 14; font.family: "Segoe UI" }
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: parent.color = "#2A2A2A"
                    onExited: parent.color = "#1A1A1A"
                }
            }
        }
    }
}

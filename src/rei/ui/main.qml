import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: mainWindow
    visible: true
    width: 900
    height: 600
    flags: Qt.Window | Qt.FramelessWindowHint
    color: "transparent"

    // Main background
    Rectangle {
        anchors.fill: parent
        color: "#0B0B0C"
        radius: 12
        border.color: Qt.rgba(229/255, 192/255, 123/255, 0.15)
        border.width: 1
        clip: true

        // Title Bar
        Rectangle {
            id: titleBar
            width: parent.width; height: 40
            color: "transparent"
            
            MouseArea {
                anchors.fill: parent
                property point clickPos: "0,0"
                onPressed: (mouse) => { clickPos = Qt.point(mouse.x, mouse.y) }
                onPositionChanged: (mouse) => {
                    mainWindow.x += mouse.x - clickPos.x
                    mainWindow.y += mouse.y - clickPos.y
                }
            }
            
            Text {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 20
                text: "Rei v2.0"
                color: Qt.rgba(1,1,1,0.4)
                font.pixelSize: 12
                font.family: "Segoe UI"
            }

            Rectangle {
                anchors.right: parent.right
                anchors.rightMargin: 15
                anchors.verticalCenter: parent.verticalCenter
                width: 30; height: 30
                radius: 15
                color: Qt.rgba(255,255,255,0.05)
                
                Text {
                    anchors.centerIn: parent
                    text: "X"
                    color: "white"
                    font.bold: true
                }
                
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: parent.color = "#E81123"
                    onExited: parent.color = Qt.rgba(255,255,255,0.05)
                    onClicked: Qt.quit()
                }
            }
        }

        // Body
        RowLayout {
            anchors.top: titleBar.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: 0

            // Sidebar
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 220
                color: "#121214"
                border.color: Qt.rgba(255,255,255,0.05)
                border.width: 1

                ColumnLayout {
                    id: sideNav
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 8
                    property int activeIndex: 0

                    Text {
                        text: "Rei"
                        color: "#E5C07B"
                        font.pixelSize: 26
                        font.bold: true
                        font.family: "Segoe UI"
                        Layout.bottomMargin: 20
                        Layout.leftMargin: 10
                    }

                    ListModel {
                        id: navModel
                        ListElement { name: "Chat"; pageIdx: 0 }
                        ListElement { name: "Activity"; pageIdx: 1 }
                        ListElement { name: "Memory"; pageIdx: 2 }
                        ListElement { name: "Capabilities"; pageIdx: 3 }
                        ListElement { name: "Settings"; pageIdx: 4 }
                    }

                    Repeater {
                        model: navModel
                        Rectangle {
                            width: parent.width; height: 42
                            radius: 8
                            color: sideNav.activeIndex === index ? Qt.rgba(229/255, 192/255, 123/255, 0.1) : "transparent"
                            
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left; anchors.leftMargin: 15
                                text: name
                                color: sideNav.activeIndex === index ? "#E5C07B" : Qt.rgba(1,1,1,0.6)
                                font.pixelSize: 14
                                font.family: "Segoe UI"
                                font.bold: sideNav.activeIndex === index
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                onEntered: { if (sideNav.activeIndex !== index) parent.color = Qt.rgba(255,255,255,0.02) }
                                onExited: { if (sideNav.activeIndex !== index) parent.color = "transparent" }
                                onClicked: sideNav.activeIndex = index
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                }
            }

            // Main Content
            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: sideNav.activeIndex

                // Page 0: Chat
                Item {
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        
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
                            spacing: 15
                            delegate: Item {
                                width: chatList.width
                                height: bubble.height
                                Rectangle {
                                    id: bubble
                                    color: isUser ? Qt.rgba(229/255,192/255,123/255,0.15) : Qt.rgba(255/255,255/255,255/255,0.05)
                                    radius: 12
                                    width: Math.min(msgLabel.implicitWidth + 30, chatList.width * 0.7)
                                    height: msgLabel.implicitHeight + 24
                                    anchors.right: isUser ? parent.right : undefined
                                    anchors.left: isUser ? undefined : parent.left

                                    Text {
                                        id: msgLabel
                                        text: msgText
                                        color: isUser ? "white" : Qt.rgba(1,1,1,0.85)
                                        anchors.centerIn: parent
                                        width: parent.width - 30
                                        wrapMode: Text.WordWrap
                                        font.pixelSize: 14
                                        font.family: "Segoe UI"
                                    }
                                }
                            }
                            onCountChanged: Qt.callLater(() => chatList.positionViewAtEnd())
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 48
                            radius: 24
                            color: Qt.rgba(255,255,255,0.03)
                            border.color: Qt.rgba(255,255,255,0.1)
                            
                            TextInput {
                                anchors.fill: parent
                                anchors.margins: 15
                                color: "white"
                                font.pixelSize: 14
                                font.family: "Segoe UI"
                                verticalAlignment: TextInput.AlignVCenter
                                clip: true
                                Text {
                                    text: "Talk or type..."
                                    color: Qt.rgba(1,1,1,0.3)
                                    visible: !parent.text
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.family: "Segoe UI"
                                    font.pixelSize: 14
                                }
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
                        Text { text: "Activity"; color: "white"; font.pixelSize: 22; font.bold: true; font.family: "Segoe UI" }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: Qt.rgba(255,255,255,0.02)
                            radius: 12
                            border.color: Qt.rgba(255,255,255,0.1)
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 25
                                spacing: 20
                                Text { text: "<font color='#E5C07B' face='monospace'>10:24</font> &nbsp;&nbsp; Opened Visual Studio Code (App)"; color: "white"; font.pixelSize: 14 }
                                Text { text: "<font color='#E5C07B' face='monospace'>10:22</font> &nbsp;&nbsp; Read file: research_paper.pdf (File)"; color: "white"; font.pixelSize: 14 }
                                Text { text: "<font color='#E5C07B' face='monospace'>10:20</font> &nbsp;&nbsp; Web request -> api.weather.com (Web)"; color: "white"; font.pixelSize: 14 }
                                Text { text: "<font color='gray' face='monospace'>10:18</font> &nbsp;&nbsp; <font color='#E81123'>Delete files (cancelled)</font>"; color: "white"; font.pixelSize: 14 }
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
                        Text { text: "Memory"; color: "white"; font.pixelSize: 22; font.bold: true; font.family: "Segoe UI" }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 42
                            radius: 21
                            color: Qt.rgba(255,255,255,0.03)
                            border.color: Qt.rgba(255,255,255,0.1)
                            Text { text: "Search memories..."; color: "gray"; anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 20; font.family: "Segoe UI"; font.pixelSize: 14 }
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: Qt.rgba(255,255,255,0.02)
                            radius: 12
                            border.color: Qt.rgba(255,255,255,0.1)
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 25
                                spacing: 25
                                Text { text: "<b>User prefers Python for coding</b><br><font color='gray'>Preference · 2 days ago</font>"; color: "white"; font.pixelSize: 14; font.family: "Segoe UI" }
                                Text { text: "<b>Lives in London</b><br><font color='gray'>Personal · 1 week ago</font>"; color: "white"; font.pixelSize: 14; font.family: "Segoe UI" }
                                Item { Layout.fillHeight: true }
                            }
                        }
                    }
                }

                // Page 3: Capabilities
                Item {
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 30
                        spacing: 20
                        Text { text: "Capabilities"; color: "white"; font.pixelSize: 22; font.bold: true; font.family: "Segoe UI" }
                        
                        GridLayout {
                            columns: 2
                            columnSpacing: 20
                            rowSpacing: 20
                            Layout.fillWidth: true
                            
                            Repeater {
                                model: ListModel {
                                    ListElement { title: "Filesystem"; desc: "Read, search, create, move, delete files." }
                                    ListElement { title: "Applications"; desc: "Open, close, control applications." }
                                    ListElement { title: "Browser"; desc: "Web search, open links, retrieve content." }
                                    ListElement { title: "System"; desc: "System information and utilities." }
                                }
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 85
                                    color: Qt.rgba(255,255,255,0.02)
                                    radius: 12
                                    border.color: Qt.rgba(255,255,255,0.1)
                                    
                                    Column {
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.left: parent.left; anchors.leftMargin: 20
                                        spacing: 4
                                        Text { text: title; color: "#E5C07B"; font.pixelSize: 15; font.bold: true; font.family: "Segoe UI" }
                                        Text { text: desc; color: "gray"; font.pixelSize: 13; font.family: "Segoe UI" }
                                    }
                                }
                            }
                        }
                        Item { Layout.fillHeight: true }
                    }
                }

                // Page 4: Settings
                Item {
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 30
                        spacing: 20
                        Text { text: "Settings"; color: "white"; font.pixelSize: 22; font.bold: true; font.family: "Segoe UI" }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 120
                            color: Qt.rgba(255,255,255,0.02)
                            radius: 12
                            border.color: Qt.rgba(255,255,255,0.1)
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 25
                                spacing: 10
                                Text { text: "Privacy Mode"; color: "white"; font.bold: true; font.pixelSize: 15; font.family: "Segoe UI" }
                                RadioButton { 
                                    text: "Local Only (No external network access)"
                                    checked: true
                                    contentItem: Text { text: parent.text; color: "white"; font.family: "Segoe UI"; leftPadding: parent.indicator.width + 10; verticalAlignment: Text.AlignVCenter }
                                }
                                RadioButton { 
                                    text: "Cloud Assisted (Uses cloud models)"
                                    contentItem: Text { text: parent.text; color: "white"; font.family: "Segoe UI"; leftPadding: parent.indicator.width + 10; verticalAlignment: Text.AlignVCenter }
                                }
                            }
                        }
                        Item { Layout.fillHeight: true }
                    }
                }
            }
        }
    }

    Window {
        id: orbWindow
        visible: true
        width: 260; height: 320
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        color: "transparent"
        x: Screen.desktopAvailableWidth - width - 30
        y: 40

        Rectangle {
            anchors.fill: parent
            color: "#0B0B0C"
            radius: 16
            border.color: Qt.rgba(229/255, 192/255, 123/255, 0.2)
            border.width: 1

            MouseArea {
                anchors.fill: parent
                property point clickPos: "0,0"
                onPressed: (mouse) => { clickPos = Qt.point(mouse.x, mouse.y) }
                onPositionChanged: (mouse) => {
                    orbWindow.x += mouse.x - clickPos.x
                    orbWindow.y += mouse.y - clickPos.y
                }
            }

            Item {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -20
                width: 100; height: 100

                // Rings (Listening)
                Repeater {
                    model: backend.state === "listening" ? 3 : 0
                    Rectangle {
                        anchors.centerIn: parent
                        width: 80; height: 80
                        radius: 40
                        color: "transparent"
                        border.color: "#E5C07B"
                        border.width: 1

                        SequentialAnimation on scale {
                            loops: Animation.Infinite
                            NumberAnimation { from: 1.0; to: 2.2; duration: 2000 }
                        }
                        SequentialAnimation on opacity {
                            loops: Animation.Infinite
                            NumberAnimation { from: 0.5; to: 0.0; duration: 2000 }
                        }
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
                        ctx.arc(width/2, height/2, 40, 0, Math.PI * 0.8);
                        ctx.strokeStyle = "#E5C07B";
                        ctx.lineWidth = 2;
                        ctx.stroke();
                    }
                    RotationAnimation on rotation {
                        from: 0; to: 360; duration: 1000; loops: Animation.Infinite; running: backend.state === "processing"
                    }
                }

                // Speaking Glow
                Rectangle {
                    anchors.centerIn: parent
                    width: 80 + (backend.volume * 60)
                    height: 80 + (backend.volume * 60)
                    radius: width/2
                    color: Qt.rgba(229/255, 192/255, 123/255, backend.volume * 0.5)
                    visible: backend.state === "speaking"
                    Behavior on width { NumberAnimation { duration: 100 } }
                    Behavior on height { NumberAnimation { duration: 100 } }
                }

                // Core Idle / Processing BG
                Rectangle {
                    anchors.centerIn: parent
                    width: 80; height: 80
                    radius: 40
                    color: "transparent"
                    border.color: backend.state === "processing" ? Qt.rgba(229/255, 192/255, 123/255, 0.2) : "#E5C07B"
                    border.width: 2
                }
            }

            Text {
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 40
                anchors.horizontalCenter: parent.horizontalCenter
                text: backend.status
                color: "white"
                font.pixelSize: 15
                font.family: "Segoe UI"
            }
        }
    }
}

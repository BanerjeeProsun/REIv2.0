import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root

    readonly property bool hasMessages: chatModel.count > 0
    readonly property bool interruptible: backend.state === "processing" || backend.state === "speaking"
    readonly property string greeting: {
        var h = new Date().getHours()
        var part = h < 5 ? "Good evening" : h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening"
        return backend.userName ? part + ", " + backend.userName + "." : part + "."
    }

    function send() {
        var t = chatInput.text.trim()
        if (t.length === 0) return
        backend.sendTextMessage(t)
        chatInput.text = ""
    }

    ListModel { id: chatModel }
    Connections {
        target: backend
        function onMessageAdded(text, is_user) {
            chatModel.append({ "msgText": text, "isUser": is_user })
        }
    }

    ColumnLayout {
        id: column
        width: Math.min(parent.width - 2 * Theme.pageMarginX, Theme.chatMaxWidth)
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: Theme.s24
        anchors.bottomMargin: Theme.s24
        spacing: 0

        // COMPACT ORB + STATUS (once a conversation has started)
        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            visible: root.hasMessages
            spacing: Theme.s10

            VoiceOrb {
                Layout.alignment: Qt.AlignHCenter
                size: 72
                onTapped: backend.interrupt()
            }
            StatusCapsule { Layout.alignment: Qt.AlignHCenter }
        }

        // CONVERSATION
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: root.hasMessages ? Theme.s16 : 0

            // Empty state: the orb on its stage above a two-tone headline
            ColumnLayout {
                anchors.centerIn: parent
                width: parent.width
                spacing: 0
                opacity: root.hasMessages ? 0 : 1
                visible: opacity > 0.001
                Behavior on opacity { NumberAnimation { duration: Theme.page; easing.type: Easing.OutCubic } }

                VoiceOrb {
                    Layout.alignment: Qt.AlignHCenter
                    size: 150
                    onTapped: backend.interrupt()
                }
                StatusCapsule {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: Theme.s4
                    Layout.bottomMargin: Theme.s32
                }

                ReiText {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    role: "display"
                    text: root.greeting
                    wrapMode: Text.WordWrap
                }
                ReiText {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    role: "display"
                    text: "What's on your mind?"
                    color: Theme.ash
                    wrapMode: Text.WordWrap
                }
                ReiText {
                    Layout.fillWidth: true
                    Layout.topMargin: Theme.s20
                    horizontalAlignment: Text.AlignHCenter
                    role: "reading"
                    text: "Speak naturally or type below."
                    color: Theme.ash
                }
            }

            ListView {
                id: chatList
                anchors.fill: parent
                model: chatModel
                spacing: Theme.s20
                clip: true
                topMargin: Theme.s8
                bottomMargin: Theme.s16
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ThinScrollBar {}

                delegate: Item {
                    id: msg
                    required property string msgText
                    required property bool isUser
                    width: chatList.width
                    height: isUser ? bubble.height : reiRow.implicitHeight

                    // Fade/slide in on arrival
                    opacity: 0
                    Component.onCompleted: enterAnim.start()
                    transform: Translate { id: shift; y: 8 }
                    ParallelAnimation {
                        id: enterAnim
                        NumberAnimation { target: msg; property: "opacity"; to: 1; duration: 180; easing.type: Easing.OutCubic }
                        NumberAnimation { target: shift; property: "y"; to: 0; duration: 180; easing.type: Easing.OutCubic }
                    }

                    // User: right-aligned Carbon bubble
                    Rectangle {
                        id: bubble
                        visible: msg.isUser
                        anchors.right: parent.right
                        width: Math.min(userText.implicitWidth + 2 * Theme.s20, msg.width * 0.72)
                        height: userText.implicitHeight + 2 * Theme.s12
                        radius: Theme.radiusNav
                        color: Theme.carbon
                        ReiText {
                            id: userText
                            anchors.fill: parent
                            anchors.leftMargin: Theme.s20
                            anchors.rightMargin: Theme.s20
                            verticalAlignment: Text.AlignVCenter
                            role: "reading"
                            text: msg.msgText
                            wrapMode: Text.Wrap
                        }
                    }

                    // Rei: left-aligned reading text beside a small lit ring
                    RowLayout {
                        id: reiRow
                        visible: !msg.isUser
                        width: msg.width * 0.86
                        spacing: Theme.s14
                        Rectangle {
                            Layout.alignment: Qt.AlignTop
                            Layout.topMargin: 6
                            Layout.preferredWidth: 12
                            Layout.preferredHeight: 12
                            radius: 6
                            color: "transparent"
                            border.color: Theme.porcelain
                            border.width: 1.5
                        }
                        ReiText {
                            Layout.fillWidth: true
                            role: "reading"
                            text: msg.msgText
                            color: Theme.porcelain
                            wrapMode: Text.Wrap
                        }
                    }
                }
                onCountChanged: Qt.callLater(() => chatList.positionViewAtEnd())
            }
        }

        // PROMPT BAR (Device Selector input: faint fill, Slate keyline, round)
        Rectangle {
            id: prompt
            Layout.fillWidth: true
            Layout.topMargin: Theme.s12
            implicitHeight: 56
            radius: height / 2
            color: promptHover.hovered && !chatInput.activeFocus ? Theme.fieldFillHover : Theme.fieldFill
            border.width: 1
            border.color: chatInput.activeFocus || promptHover.hovered ? Theme.ash : Theme.slate
            Behavior on color { ColorAnimation { duration: Theme.fast } }
            Behavior on border.color { ColorAnimation { duration: Theme.fast } }

            HoverHandler { id: promptHover; cursorShape: Qt.IBeamCursor }
            TapHandler { onTapped: chatInput.forceActiveFocus() }
            FocusRing { shown: chatInput.activeFocus; baseRadius: prompt.radius }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Theme.s24
                anchors.rightMargin: Theme.s10
                spacing: Theme.s12

                // Live indicator: breathes while the mic is listening
                Rectangle {
                    Layout.preferredWidth: 6
                    Layout.preferredHeight: 6
                    Layout.alignment: Qt.AlignVCenter
                    radius: 3
                    color: backend.state === "idle" ? Theme.ash : Theme.porcelain
                    SequentialAnimation on opacity {
                        running: backend.state === "listening"
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.3; duration: 800; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 800; easing.type: Easing.InOutSine }
                    }
                }

                TextInput {
                    id: chatInput
                    objectName: "chatInput"
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    verticalAlignment: TextInput.AlignVCenter
                    color: Theme.porcelain
                    selectionColor: Theme.alpha(Theme.appleBlue, 0.55)
                    selectedTextColor: Theme.white
                    font.family: Theme.fontText
                    font.pixelSize: Theme.type.reading.size
                    font.letterSpacing: Theme.type.reading.tracking
                    clip: true
                    focus: true
                    activeFocusOnTab: true
                    onAccepted: root.send()

                    ReiText {
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width
                        elide: Text.ElideRight
                        role: "reading"
                        color: Theme.ash
                        visible: chatInput.text.length === 0
                        text: backend.state === "speaking" ? "Speaking. Press Esc or say “stop”"
                            : backend.state === "processing" ? "Thinking. Press Esc to stop"
                            : backend.state === "listening" ? "Listening… or type a message"
                            : "Message Rei"
                    }
                }

                // Esc keycap, shown while there is something to stop
                Rectangle {
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: escLabel.implicitWidth + 2 * Theme.s6
                    Layout.preferredHeight: 20
                    radius: Theme.radiusKey
                    color: "transparent"
                    border.width: 1
                    border.color: Theme.steel
                    visible: opacity > 0.001
                    opacity: root.interruptible ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: Theme.fast } }
                    ReiText {
                        id: escLabel
                        anchors.centerIn: parent
                        role: "utilityNav"
                        text: "Esc"
                        color: Theme.ash
                    }
                }

                // One slot, three faces: mic (idle) / send (text) / stop (busy)
                Item {
                    id: actionSlot
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: Qt.AlignVCenter
                    readonly property bool canSend: chatInput.text.trim().length > 0
                    readonly property string face: canSend ? "send" : root.interruptible ? "stop" : "mic"

                    Icon {
                        anchors.centerIn: parent
                        source: "../icons/mic.svg"
                        size: 18
                        color: backend.state === "listening" ? Theme.porcelain : Theme.ash
                        opacity: actionSlot.face === "mic" ? 1 : 0
                        scale: actionSlot.face === "mic" ? 1 : 0.6
                        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
                        Behavior on scale { NumberAnimation { duration: Theme.fast; easing.type: Easing.OutCubic } }
                    }

                    IconButton {
                        id: sendButton
                        anchors.fill: parent
                        variant: "primary"
                        iconSource: Qt.resolvedUrl("../icons/send.svg")
                        iconSize: 16
                        iconOffsetX: -1
                        tooltip: "Send"
                        enabled: actionSlot.face === "send"
                        visible: opacity > 0.001
                        opacity: actionSlot.face === "send" ? 1 : 0
                        scale: actionSlot.face === "send" ? (pressed ? 0.96 : 1) : 0.6
                        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
                        onClicked: root.send()
                    }

                    IconButton {
                        id: stopButton
                        objectName: "stopButton"
                        anchors.fill: parent
                        variant: "capsule"
                        iconSource: Qt.resolvedUrl("../icons/stop.svg")
                        iconSize: 14
                        tooltip: "Stop"
                        enabled: actionSlot.face === "stop"
                        visible: opacity > 0.001
                        opacity: actionSlot.face === "stop" ? 1 : 0
                        scale: actionSlot.face === "stop" ? (pressed ? 0.96 : 1) : 0.6
                        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
                        onClicked: backend.interrupt()
                    }
                }
            }
        }
    }
}

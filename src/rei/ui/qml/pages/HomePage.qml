import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Item {
    id: root

    readonly property bool hasMessages: chatModel.count > 0
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
        width: Math.min(parent.width - 2 * Theme.pageMarginX, Theme.pageMaxWidth)
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: 28
        anchors.bottomMargin: 28
        spacing: 0

        // COMPACT ORB + STATUS (once a conversation has started).
        // The block itself is centred: a nested layout is only as wide as its
        // children, so centring the children inside it would do nothing.
        ColumnLayout {
            Layout.alignment: Qt.AlignHCenter
            visible: root.hasMessages
            spacing: 10

            VoiceOrb {
                Layout.alignment: Qt.AlignHCenter
                size: 88
            }

            Tag {
                Layout.alignment: Qt.AlignHCenter
                text: backend.status
                ink: Theme.textBody
                dot: true
                dotColor: backend.state === "idle" ? Theme.textMuted : Theme.coral
            }
        }

        // CONVERSATION
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: root.hasMessages ? 16 : 0

            // Empty state: large orb anchoring an editorial two-tone headline
            ColumnLayout {
                anchors.centerIn: parent
                width: parent.width
                spacing: 2
                opacity: root.hasMessages ? 0 : 1
                visible: opacity > 0.001
                Behavior on opacity { NumberAnimation { duration: Theme.page; easing.type: Easing.OutCubic } }

                VoiceOrb {
                    Layout.alignment: Qt.AlignHCenter
                    size: 150
                }
                Tag {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    Layout.bottomMargin: 28
                    text: backend.status
                    ink: Theme.textBody
                    dot: true
                    dotColor: backend.state === "idle" ? Theme.textMuted : Theme.coral
                }

                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: root.greeting
                    color: Theme.textPrimary
                    font.family: Theme.fontDisplay
                    font.pixelSize: 48
                    font.weight: Font.DemiBold
                    font.letterSpacing: Theme.tracking(48)
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: "What's on your mind?"
                    color: Theme.coral
                    font.family: Theme.fontDisplay
                    font.pixelSize: 48
                    font.weight: Font.DemiBold
                    font.letterSpacing: Theme.tracking(48)
                }
                Text {
                    Layout.fillWidth: true
                    Layout.topMargin: 16
                    horizontalAlignment: Text.AlignHCenter
                    text: "Speak naturally or type below."
                    color: Theme.textSecondary
                    font.family: Theme.fontText
                    font.pixelSize: Theme.sizeBody
                }
            }

            ListView {
                id: chatList
                anchors.fill: parent
                model: chatModel
                spacing: 18
                clip: true
                topMargin: 8
                bottomMargin: 16
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

                    // User: right-aligned plum bubble
                    Rectangle {
                        id: bubble
                        visible: msg.isUser
                        anchors.right: parent.right
                        width: Math.min(userText.implicitWidth + 36, msg.width * 0.72)
                        height: userText.implicitHeight + 24
                        radius: Theme.radiusCard
                        color: Theme.elevated
                        Text {
                            id: userText
                            anchors.fill: parent
                            anchors.leftMargin: 18
                            anchors.rightMargin: 18
                            verticalAlignment: Text.AlignVCenter
                            text: msg.msgText
                            color: Theme.textPrimary
                            font.family: Theme.fontText
                            font.pixelSize: Theme.sizeBody
                            lineHeight: 1.35
                            wrapMode: Text.Wrap
                        }
                    }

                    // Rei: left-aligned text with a small ember glyph on the first line
                    RowLayout {
                        id: reiRow
                        visible: !msg.isUser
                        width: msg.width * 0.86
                        spacing: 14
                        Rectangle {
                            Layout.alignment: Qt.AlignTop
                            Layout.topMargin: 4
                            Layout.preferredWidth: 14
                            Layout.preferredHeight: 14
                            radius: 7
                            color: "transparent"
                            border.color: Theme.coral
                            border.width: 2
                        }
                        Text {
                            Layout.fillWidth: true
                            text: msg.msgText
                            color: Theme.textBody
                            font.family: Theme.fontText
                            font.pixelSize: Theme.sizeBody
                            lineHeight: 1.4
                            wrapMode: Text.Wrap
                            textFormat: Text.PlainText
                        }
                    }
                }
                onCountChanged: Qt.callLater(() => chatList.positionViewAtEnd())
            }
        }

        // PROMPT BAR (AI Prompt Input: pill, coral dot, mic/send on the right)
        Rectangle {
            id: prompt
            Layout.fillWidth: true
            Layout.topMargin: 12
            implicitHeight: 60
            radius: Theme.radiusPill
            color: chatInput.activeFocus ? Theme.elevatedHover : promptHover.hovered ? Qt.darker(Theme.elevatedHover, 1.06) : Theme.elevated
            border.width: 1
            border.color: chatInput.activeFocus ? Theme.coralAlpha(0.55) : Theme.hairline
            Behavior on color { ColorAnimation { duration: Theme.fast } }
            Behavior on border.color { ColorAnimation { duration: Theme.fast } }

            HoverHandler { id: promptHover; cursorShape: Qt.IBeamCursor }
            TapHandler { onTapped: chatInput.forceActiveFocus() }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 10
                spacing: 14

                // AI indicator: pulses while the mic is live
                Rectangle {
                    Layout.preferredWidth: 8
                    Layout.preferredHeight: 8
                    Layout.alignment: Qt.AlignVCenter
                    radius: 4
                    color: Theme.coral
                    SequentialAnimation on opacity {
                        running: backend.state === "listening"
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.35; duration: 700; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 700; easing.type: Easing.InOutSine }
                    }
                }

                TextInput {
                    id: chatInput
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter
                    verticalAlignment: TextInput.AlignVCenter
                    color: Theme.textPrimary
                    selectionColor: Theme.coralAlpha(0.45)
                    selectedTextColor: Theme.textPrimary
                    font.family: Theme.fontText
                    font.pixelSize: Theme.sizeBody
                    clip: true
                    focus: true
                    onAccepted: root.send()

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: backend.state === "listening" ? "Listening… or type a message" : "Message Rei"
                        color: Theme.textMuted
                        visible: chatInput.text.length === 0
                        font: chatInput.font
                    }
                }

                // Mic state when empty, coral send button when there's text
                Item {
                    id: actionSlot
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 40
                    Layout.alignment: Qt.AlignVCenter
                    readonly property bool canSend: chatInput.text.trim().length > 0

                    Icon {
                        anchors.centerIn: parent
                        source: "../icons/mic.svg"
                        size: 18
                        color: backend.state === "listening" ? Theme.textBody : Theme.textMuted
                        opacity: actionSlot.canSend ? 0 : 1
                        scale: actionSlot.canSend ? 0.6 : 1
                        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
                        Behavior on scale { NumberAnimation { duration: Theme.fast; easing.type: Easing.OutCubic } }
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 20
                        color: sendMouse.pressed ? Theme.coralPressed : sendMouse.containsMouse ? Theme.coralHover : Theme.coral
                        opacity: actionSlot.canSend ? 1 : 0
                        scale: !actionSlot.canSend ? 0.6 : sendMouse.pressed ? 0.92 : 1
                        visible: opacity > 0.001
                        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
                        Behavior on scale { NumberAnimation { duration: Theme.fast; easing.type: Easing.OutCubic } }
                        Behavior on color { ColorAnimation { duration: Theme.fast } }
                        Icon {
                            anchors.centerIn: parent
                            anchors.horizontalCenterOffset: -1
                            source: "../icons/send.svg"
                            size: 16
                            color: Theme.textPrimary
                        }
                        MouseArea {
                            id: sendMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.send()
                        }
                    }
                }
            }
        }
    }
}

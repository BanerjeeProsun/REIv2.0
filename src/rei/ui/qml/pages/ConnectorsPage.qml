import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    id: page
    title: "Connectors"
    subtitle: "Services Rei can use for you. Credentials stay in Windows Credential Manager."

    readonly property bool offline: backend.privacyModeText === "Local Only"

    function iconFor(cid) {
        return cid === "email" ? "../icons/mail.svg"
             : cid === "youtube" || cid === "spotify" ? "../icons/music.svg"
             : "../icons/connectors.svg"
    }

    // Local Only blocks all network access, including connectors
    SurfaceCard {
        visible: page.offline
        padding: 20
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.s16
            Icon {
                Layout.alignment: Qt.AlignVCenter
                source: Qt.resolvedUrl("../icons/local.svg")
                size: 20
                color: Theme.coral
            }
            Text {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                text: "You're in Local Only mode, so connectors can't go online."
                color: Theme.textBody
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBodySm
                wrapMode: Text.WordWrap
            }
            PillButton {
                text: "Use Local + Connectors"
                small: true
                variant: "primary"
                onClicked: backend.setPrivacyMode("Local + Connectors")
            }
        }
    }

    Repeater {
        model: typeof connectorModel !== "undefined" ? connectorModel : 0

        SettingRow {
            id: row
            readonly property string cid: model.cid
            readonly property bool connected: model.connected
            readonly property var fieldList: model.fields

            title: model.name
            description: model.connected && model.detail ? model.detail
                       : model.error ? model.error
                       : model.description
            iconSource: Qt.resolvedUrl(page.iconFor(model.cid))

            Tag {
                text: row.connected ? "Connected" : "Not connected"
                dot: true
                dotColor: row.connected ? Theme.coral : Theme.textMuted
            }
            PillButton {
                text: row.connected ? "Disconnect" : "Connect"
                small: true
                variant: row.connected ? "ghost" : "outline"
                onClicked: {
                    if (row.connected) backend.disconnectConnector(row.cid)
                    else if (row.fieldList.length === 0) backend.connectConnector(row.cid, "{}")
                    else connectDialog.openFor(row.cid, model.name, row.fieldList, model.note)
                }
            }
        }
    }

    // CONNECT FORM
    Popup {
        id: connectDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(460, parent ? parent.width - 80 : 460)
        padding: 28
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape

        property string cid: ""
        property string title: ""
        property var fields: []
        property string note: ""
        property bool busy: false
        property string errorText: ""

        function openFor(id, name, fieldList, noteText) {
            cid = id; title = name; fields = fieldList; note = noteText
            busy = false; errorText = ""
            open()
        }
        function submit() {
            var values = {}
            for (var i = 0; i < fieldRepeater.count; i++) {
                var f = fieldRepeater.itemAt(i)
                values[f.key] = f.text
            }
            busy = true; errorText = ""
            backend.connectConnector(cid, JSON.stringify(values))
        }

        Overlay.modal: Rectangle { color: Qt.rgba(8 / 255, 8 / 255, 14 / 255, 0.6) }
        enter: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.page; easing.type: Easing.OutCubic }
                NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: Theme.page; easing.type: Easing.OutCubic }
            }
        }
        exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: Theme.exit } }
        background: Rectangle { color: Theme.elevated; radius: Theme.radiusCard; border.color: Theme.hairline }

        contentItem: ColumnLayout {
            spacing: 18

            Text {
                Layout.fillWidth: true
                text: "Connect " + connectDialog.title
                color: Theme.textPrimary
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.sizeHeadingSm
                font.weight: Font.DemiBold
                font.letterSpacing: Theme.tracking(Theme.sizeHeadingSm)
            }
            Text {
                Layout.fillWidth: true
                visible: connectDialog.note !== ""
                text: connectDialog.note
                color: Theme.textSecondary
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBodySm
                lineHeight: 1.3
                wrapMode: Text.WordWrap
            }

            Repeater {
                id: fieldRepeater
                model: connectDialog.fields
                InputField {
                    required property var modelData
                    readonly property string key: modelData.key
                    label: modelData.label + (modelData.optional ? " (optional)" : "")
                    placeholder: modelData.placeholder
                    secret: modelData.secret
                    onAccepted: connectDialog.submit()
                }
            }

            Text {
                Layout.fillWidth: true
                visible: connectDialog.errorText !== ""
                text: connectDialog.errorText
                color: Theme.coral
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBodySm
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 4
                spacing: 8
                Item { Layout.fillWidth: true }
                PillButton { text: "Cancel"; variant: "ghost"; onClicked: connectDialog.close() }
                PillButton {
                    text: connectDialog.busy ? "Connecting..." : "Connect"
                    variant: "primary"
                    enabled: !connectDialog.busy
                    onClicked: connectDialog.submit()
                }
            }
        }

        Connections {
            target: backend
            function onConnectorResult(cid, ok, message) {
                if (cid !== connectDialog.cid || !connectDialog.opened) return
                connectDialog.busy = false
                if (ok) connectDialog.close()
                else connectDialog.errorText = message
            }
        }
    }
}

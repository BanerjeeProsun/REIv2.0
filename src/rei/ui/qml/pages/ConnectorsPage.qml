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
        outlined: true
        padding: Theme.s20
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.s16
            Icon {
                Layout.alignment: Qt.AlignVCenter
                source: Qt.resolvedUrl("../icons/local.svg")
                size: 20
                color: Theme.porcelain
            }
            ReiText {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                role: "body"
                text: "You're in Local Only mode, so connectors can't go online."
                color: Theme.porcelain
                wrapMode: Text.WordWrap
            }
            PillButton {
                text: "Use Local + Connectors"
                small: true
                variant: "capsule"
                // Opens the privacy dialog; nothing changes until confirmed
                onClicked: backend.requestPrivacyMode("Local + Connectors")
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
                dotColor: row.connected ? Theme.porcelain : Theme.ash
                ink: row.connected ? Theme.porcelain : Theme.ash
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
    ReiDialog {
        id: connectDialog
        title: "Connect " + name
        subtitle: note
        preferredWidth: 480
        escClosable: !busy

        property string cid: ""
        property string name: ""
        property var fields: []
        property string note: ""
        property bool busy: false
        property string errorText: ""

        function openFor(id, connectorName, fieldList, noteText) {
            cid = id; name = connectorName; fields = fieldList; note = noteText || ""
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
        onOpened: if (fieldRepeater.count > 0) fieldRepeater.itemAt(0).input.forceActiveFocus()

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

        ReiText {
            Layout.fillWidth: true
            visible: connectDialog.errorText !== ""
            role: "body"
            text: connectDialog.errorText
            color: Theme.alert
            wrapMode: Text.WordWrap
        }

        buttons: [
            PillButton { text: "Cancel"; variant: "outline"; onClicked: connectDialog.close() },
            PillButton {
                text: connectDialog.busy ? "Connecting…" : "Connect"
                variant: "primary"
                enabled: !connectDialog.busy
                onClicked: connectDialog.submit()
            }
        ]

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

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

// The one modal frame for every dialog: a Carbon panel with 28px corners and a
// Steel keyline on a dimmed black stage. No shadow (DESIGN.md elevation).
// Remembers what had focus and gives it back on close, and tells the window a
// dialog is open so window-level Esc (interrupt) leaves Esc to the dialog.
Popup {
    id: root
    property string title: ""
    property string subtitle: ""
    property bool escClosable: true
    property int preferredWidth: 480
    default property alias content: body.data
    property alias buttons: buttonRow.data

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(preferredWidth, (parent ? parent.width : preferredWidth + 80) - 80)
    padding: Theme.s32
    modal: true
    focus: true
    closePolicy: escClosable ? (Popup.CloseOnEscape | Popup.CloseOnPressOutside) : Popup.NoAutoClose

    property var _restoreFocus: null
    property bool _counted: false
    readonly property var _window: ApplicationWindow.window

    onAboutToShow: {
        _restoreFocus = _window ? _window.activeFocusItem : null
        if (_window && _window.dialogDepth !== undefined && !_counted) {
            _window.dialogDepth += 1
            _counted = true
        }
    }
    onClosed: {
        if (_counted && _window && _window.dialogDepth !== undefined) {
            _window.dialogDepth = Math.max(0, _window.dialogDepth - 1)
        }
        _counted = false
        var item = _restoreFocus
        _restoreFocus = null
        if (item && typeof item.forceActiveFocus === "function") item.forceActiveFocus()
    }

    Overlay.modal: Rectangle { color: Theme.scrim }

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.page; easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: 0.98; to: 1; duration: Theme.page; easing.type: Easing.OutCubic }
        }
    }
    exit: Transition {
        NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.exit; easing.type: Easing.OutCubic }
    }

    background: Rectangle {
        color: Theme.carbon
        radius: Theme.radiusCard
        border.width: 1
        border.color: Theme.steel
    }

    contentItem: ColumnLayout {
        spacing: Theme.s24

        ColumnLayout {
            Layout.fillWidth: true
            spacing: Theme.s8
            ReiText {
                Layout.fillWidth: true
                role: "featureStat"
                text: root.title
                wrapMode: Text.WordWrap
            }
            ReiText {
                Layout.fillWidth: true
                visible: root.subtitle !== ""
                role: "body"
                text: root.subtitle
                color: Theme.ash
                wrapMode: Text.WordWrap
            }
        }

        ColumnLayout {
            id: body
            Layout.fillWidth: true
            spacing: Theme.s12
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.s8
            Item { Layout.fillWidth: true }
            RowLayout {
                id: buttonRow
                spacing: Theme.s8
            }
        }
    }
}

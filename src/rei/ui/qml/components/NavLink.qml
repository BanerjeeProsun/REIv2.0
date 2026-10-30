import QtQuick
import ".."

// Utility-bar link (DESIGN.md Global Utility Navigation): 12px label at 80%
// white, Porcelain on hover; the current page gets weight and a hairline
// underline rather than a coloured pill.
Item {
    id: root
    property string text: ""
    property bool active: false
    property string shortcutHint: ""
    signal clicked()

    readonly property bool hovered: mouse.containsMouse

    implicitWidth: label.implicitWidth + 2 * Theme.s10
    implicitHeight: Theme.topBarHeight
    activeFocusOnTab: true
    Accessible.role: Accessible.PageTab
    Accessible.name: root.text

    ReiText {
        id: label
        anchors.centerIn: parent
        role: "utilityNav"
        text: root.text
        color: root.active || root.hovered ? Theme.porcelain : Theme.navInk
        font.weight: root.active ? 600 : 400
    }

    // Underline grows from the centre when the page becomes current
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
        height: 1
        width: root.active ? label.implicitWidth : 0
        color: Theme.porcelain
        opacity: root.active ? 1 : 0
        Behavior on width { NumberAnimation { duration: Theme.page; easing.type: Easing.OutCubic } }
        Behavior on opacity { NumberAnimation { duration: Theme.fast } }
    }

    // Focus ring hugs the label, not the whole bar height
    Item {
        anchors.centerIn: parent
        width: label.implicitWidth + 16
        height: 24
        FocusRing { shown: root.activeFocus; baseRadius: Theme.radiusLink }
    }

    ReiToolTip {
        visible: root.shortcutHint !== "" && mouse.containsMouse
        text: root.shortcutHint
    }

    Keys.onReturnPressed: root.clicked()
    Keys.onEnterPressed: root.clicked()
    Keys.onSpacePressed: root.clicked()

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}

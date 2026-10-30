import QtQuick
import QtQuick.Layouts
import ".."

// Small translucent pill for categories and status (12px, fully round).
Rectangle {
    id: root
    property string text: ""
    property color ink: Theme.ash
    property color fill: Theme.alpha(Theme.steel, 0.6)
    property bool dot: false
    property color dotColor: ink

    implicitHeight: 24
    implicitWidth: row.implicitWidth + 2 * Theme.s10
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight
    Layout.alignment: Qt.AlignVCenter
    radius: height / 2
    color: fill

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: Theme.s6
        Rectangle {
            visible: root.dot
            Layout.preferredWidth: 6
            Layout.preferredHeight: 6
            radius: 3
            color: root.dotColor
            Layout.alignment: Qt.AlignVCenter
        }
        ReiText {
            Layout.alignment: Qt.AlignVCenter
            role: "utilityNav"
            text: root.text
            color: root.ink
        }
    }
}

import QtQuick
import QtQuick.Layouts
import ".."

// Pill tag for categories and status (100px radius, 12px medium text).
Rectangle {
    id: root
    property string text: ""
    property color ink: Theme.textSecondary
    property color fill: Qt.rgba(1, 1, 1, 0.05)
    property bool dot: false
    property color dotColor: ink

    implicitHeight: 24
    implicitWidth: row.implicitWidth + 20
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight
    Layout.alignment: Qt.AlignVCenter
    radius: height / 2
    color: fill

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: 6
        Rectangle {
            visible: root.dot
            width: 6; height: 6; radius: 3
            color: root.dotColor
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: root.text
            color: root.ink
            font.family: Theme.fontText
            font.pixelSize: Theme.sizeCaption
            font.weight: Font.Medium
            Layout.alignment: Qt.AlignVCenter
        }
    }
}

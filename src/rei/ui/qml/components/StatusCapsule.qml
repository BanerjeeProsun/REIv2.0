import QtQuick
import QtQuick.Layouts
import ".."

// Rei's state line as a translucent capsule (DESIGN.md Dark Pricing Capsule):
// a dot that breathes while the mic is live, then the status text.
Rectangle {
    id: root
    property string text: backend.status
    property string st: backend.state

    implicitHeight: 28
    implicitWidth: row.implicitWidth + 2 * Theme.s12
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight
    radius: height / 2
    color: Theme.capsule
    onStChanged: if (st !== "listening") dot.opacity = 1

    RowLayout {
        id: row
        anchors.centerIn: parent
        spacing: Theme.s8
        Rectangle {
            id: dot
            Layout.preferredWidth: 6
            Layout.preferredHeight: 6
            Layout.alignment: Qt.AlignVCenter
            radius: 3
            color: root.st === "idle" ? Theme.ash : Theme.porcelain
            Behavior on color { ColorAnimation { duration: Theme.fast } }
            SequentialAnimation on opacity {
                running: root.st === "listening"
                loops: Animation.Infinite
                NumberAnimation { to: 0.3; duration: 800; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 800; easing.type: Easing.InOutSine }
            }
        }
        ReiText {
            Layout.alignment: Qt.AlignVCenter
            role: "utilityNav"
            text: root.text
            color: Theme.navInk
        }
    }
}

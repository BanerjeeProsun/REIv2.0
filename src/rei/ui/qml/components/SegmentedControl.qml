import QtQuick
import QtQuick.Layouts
import ".."

// Pill switch with a sliding Steel thumb on a Graphite track.
// Display-only: it emits selected(index) and shows currentIndex, so a caller
// that asks for confirmation first simply keeps currentIndex bound.
Rectangle {
    id: root
    property var options: []
    property int currentIndex: 0
    signal selected(int index)

    property int segmentWidth: 112
    implicitWidth: segmentWidth * options.length + 8
    implicitHeight: 36
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight
    radius: height / 2
    color: Theme.graphite
    border.width: 1
    border.color: Theme.steel
    activeFocusOnTab: true

    Keys.onLeftPressed: if (currentIndex > 0) selected(currentIndex - 1)
    Keys.onRightPressed: if (currentIndex < options.length - 1) selected(currentIndex + 1)
    FocusRing { shown: root.activeFocus; baseRadius: root.radius }

    Rectangle {
        id: thumb
        y: 4
        x: 4 + root.currentIndex * root.segmentWidth
        width: root.segmentWidth
        height: parent.height - 8
        radius: height / 2
        color: Theme.steel
        Behavior on x { NumberAnimation { duration: Theme.page; easing.type: Easing.OutCubic } }
    }

    Row {
        x: 4
        anchors.verticalCenter: parent.verticalCenter
        Repeater {
            model: root.options
            Item {
                width: root.segmentWidth
                height: 28
                readonly property bool isCurrent: index === root.currentIndex
                ReiText {
                    anchors.centerIn: parent
                    role: "utilityNav"
                    text: modelData
                    color: parent.isCurrent || segMouse.containsMouse ? Theme.porcelain : Theme.ash
                    font.weight: parent.isCurrent ? 600 : 400
                }
                MouseArea {
                    id: segMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: parent.isCurrent ? Qt.ArrowCursor : Qt.PointingHandCursor
                    onClicked: if (!parent.isCurrent) root.selected(index)
                }
            }
        }
    }
}

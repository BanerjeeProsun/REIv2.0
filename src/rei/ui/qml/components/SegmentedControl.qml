import QtQuick
import QtQuick.Layouts
import ".."

// Two-or-more option pill switch with a sliding thumb.
Rectangle {
    id: root
    property var options: []
    property int currentIndex: 0
    signal selected(int index)

    readonly property int segmentWidth: 128
    implicitWidth: segmentWidth * options.length + 8
    implicitHeight: 40
    Layout.preferredWidth: implicitWidth
    Layout.preferredHeight: implicitHeight
    radius: height / 2
    color: Theme.recessed

    Rectangle {
        id: thumb
        y: 4
        x: 4 + root.currentIndex * root.segmentWidth
        width: root.segmentWidth
        height: parent.height - 8
        radius: height / 2
        color: Theme.elevatedHover
        border.color: Theme.hairlineStrong
        Behavior on x { NumberAnimation { duration: Theme.page; easing.type: Easing.OutCubic } }
    }

    Row {
        x: 4
        anchors.verticalCenter: parent.verticalCenter
        Repeater {
            model: root.options
            Item {
                width: root.segmentWidth
                height: 32
                readonly property bool isCurrent: index === root.currentIndex
                Text {
                    anchors.centerIn: parent
                    text: modelData
                    color: parent.isCurrent ? Theme.textPrimary : segMouse.containsMouse ? Theme.textBody : Theme.textSecondary
                    font.family: Theme.fontText
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    Behavior on color { ColorAnimation { duration: Theme.fast } }
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

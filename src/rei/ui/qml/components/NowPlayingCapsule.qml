import QtQuick
import QtQuick.Layouts
import ".."

// Now playing (in-app YouTube player or Spotify) as a translucent capsule in
// the utility bar. Only present while something is playing.
Item {
    id: root
    property int maxTitleWidth: 180
    readonly property bool playing: backend.nowPlaying !== ""

    implicitHeight: 28
    implicitWidth: playing ? row.implicitWidth + Theme.s12 + Theme.s4 : 0
    visible: opacity > 0.001
    opacity: playing ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: Theme.page } }

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: Theme.capsule
    }

    RowLayout {
        id: row
        anchors.left: parent.left
        anchors.leftMargin: Theme.s12
        anchors.verticalCenter: parent.verticalCenter
        spacing: Theme.s6

        Icon {
            Layout.alignment: Qt.AlignVCenter
            source: Qt.resolvedUrl("../icons/music.svg")
            size: 12
            color: Theme.porcelain
            // Gentle pulse while playing
            SequentialAnimation on opacity {
                running: root.playing && !backend.nowPlayingPaused
                loops: Animation.Infinite
                NumberAnimation { to: 0.45; duration: 700; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 700; easing.type: Easing.InOutSine }
            }
        }
        ReiText {
            Layout.alignment: Qt.AlignVCenter
            Layout.maximumWidth: root.maxTitleWidth
            role: "utilityNav"
            text: backend.nowPlaying + (backend.nowPlayingPaused ? " · Paused" : "")
            color: Theme.navInk
            elide: Text.ElideRight
        }
        IconButton {
            Layout.alignment: Qt.AlignVCenter
            size: 24
            iconSize: 10
            iconSource: Qt.resolvedUrl(backend.nowPlayingPaused ? "../icons/play.svg" : "../icons/pause.svg")
            tooltip: backend.nowPlayingPaused ? "Play" : "Pause"
            onClicked: backend.sendPlayerCommand("toggle")
        }
        IconButton {
            Layout.alignment: Qt.AlignVCenter
            size: 24
            iconSize: 10
            iconSource: Qt.resolvedUrl("../icons/stop.svg")
            tooltip: "Stop music"
            onClicked: backend.sendPlayerCommand("stop")
        }
    }
}

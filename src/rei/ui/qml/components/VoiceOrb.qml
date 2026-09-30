import QtQuick
import ".."

// Rei's voice orb. Always alive: breathes at rest, orbits while thinking,
// ripples while listening (following mic level), and blooms with Rei's own
// voice amplitude while speaking. Only transform/opacity animate (GPU-cheap,
// no relayout), so it holds 60fps.
Item {
    id: orb
    property int size: 140
    property string st: backend.state
    implicitWidth: size
    implicitHeight: size

    // Live amplitude: mic while listening, Rei's own voice while speaking
    property real level: Math.max(st === "listening" ? backend.volume : 0, backend.outputLevel)
    Behavior on level { NumberAnimation { duration: 80 } }

    property real breath: 0
    SequentialAnimation on breath {
        loops: Animation.Infinite
        NumberAnimation { from: 0; to: 1; duration: 1800; easing.type: Easing.InOutSine }
        NumberAnimation { from: 1; to: 0; duration: 1800; easing.type: Easing.InOutSine }
    }

    property real pulse: 0
    SequentialAnimation on pulse {
        running: orb.st === "speaking" || orb.st === "processing"
        loops: Animation.Infinite
        NumberAnimation { from: 0.0; to: 1.0; duration: 380; easing.type: Easing.InOutQuad }
        NumberAnimation { from: 1.0; to: 0.4; duration: 300; easing.type: Easing.InOutQuad }
        NumberAnimation { from: 0.4; to: 0.9; duration: 460; easing.type: Easing.InOutQuad }
        NumberAnimation { from: 0.9; to: 0.0; duration: 420; easing.type: Easing.InOutQuad }
    }

    readonly property real energy: st === "speaking" ? Math.max(level, pulse * 0.6)
                                 : st === "processing" ? pulse * 0.3
                                 : st === "listening" ? Math.max(level, 0.18 * breath)
                                 : 0.12 * breath

    // Everything below is drawn at a fixed 160px design size and scaled.
    Item {
        id: canvas
        width: 160; height: 160
        anchors.centerIn: parent
        scale: orb.size / 160

        // Soft outer bloom
        Rectangle {
            anchors.centerIn: parent
            width: 104; height: 104; radius: 52
            color: Theme.coralAlpha(0.10 + 0.30 * orb.energy)
            scale: 1.0 + 0.06 * orb.breath + 0.45 * orb.energy
            Behavior on scale { NumberAnimation { duration: 90 } }
        }

        // Inner glow
        Rectangle {
            anchors.centerIn: parent
            width: 104; height: 104; radius: 52
            color: Theme.coralAlpha(0.14 + 0.22 * orb.energy)
            scale: 0.78 + 0.16 * orb.energy + 0.03 * orb.breath
            Behavior on scale { NumberAnimation { duration: 90 } }
        }

        // Core
        Rectangle {
            anchors.centerIn: parent
            width: 104; height: 104; radius: 52
            color: Theme.canvas
            scale: 0.62
            border.width: 2
            border.color: orb.st === "processing" ? Theme.coralAlpha(0.35) : Theme.coral
            Behavior on border.color { ColorAnimation { duration: Theme.fast } }
        }

        // Listening ripples, staggered
        Repeater {
            model: 2
            Rectangle {
                anchors.centerIn: parent
                width: 104; height: 104; radius: 52
                color: "transparent"
                border.color: Theme.coral
                border.width: 1
                opacity: 0
                visible: orb.st === "listening"
                SequentialAnimation on scale {
                    running: orb.st === "listening"
                    loops: Animation.Infinite
                    PauseAnimation { duration: index * 1100 }
                    NumberAnimation { from: 0.9; to: 1.6; duration: 2200; easing.type: Easing.OutCubic }
                }
                SequentialAnimation on opacity {
                    running: orb.st === "listening"
                    loops: Animation.Infinite
                    PauseAnimation { duration: index * 1100 }
                    NumberAnimation { from: 0.45; to: 0.0; duration: 2200; easing.type: Easing.OutCubic }
                }
            }
        }

        // Thinking arc
        Canvas {
            id: arc
            anchors.fill: parent
            visible: orb.st === "processing"
            onVisibleChanged: if (visible) requestPaint()
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.beginPath()
                ctx.arc(width / 2, height / 2, 58, 0, Math.PI * 0.65)
                ctx.strokeStyle = Theme.coral
                ctx.lineWidth = 2
                ctx.lineCap = "round"
                ctx.stroke()
            }
            RotationAnimation on rotation {
                from: 0; to: 360; duration: 1100
                loops: Animation.Infinite
                running: orb.st === "processing"
            }
        }
    }
}

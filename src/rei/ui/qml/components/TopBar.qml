import QtQuick
import QtQuick.Layouts
import ".."

// 44px global utility bar (DESIGN.md): black, compact 12px links, a single
// rgb(40,40,40) keyline underneath. Wordmark left, pages centred, now-playing
// and the privacy mode on the right.
Rectangle {
    id: root
    property var pages: []
    property int currentPage: 0
    signal pageSelected(int index)

    // Centred links need room on both sides; the now-playing capsule takes some
    readonly property bool narrow: width < (backend.nowPlaying !== "" ? 1320 : 1060)

    implicitHeight: Theme.topBarHeight
    color: Theme.obsidian

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 1
        color: Theme.keyline
    }

    // Wordmark: a small lit ring, like the orb, plus "Rei"
    RowLayout {
        id: brand
        anchors.left: parent.left
        anchors.leftMargin: Theme.s20
        anchors.verticalCenter: parent.verticalCenter
        spacing: Theme.s8
        Rectangle {
            Layout.preferredWidth: 14
            Layout.preferredHeight: 14
            Layout.alignment: Qt.AlignVCenter
            radius: 7
            color: "transparent"
            border.color: Theme.porcelain
            border.width: 1.5
            Rectangle {
                anchors.centerIn: parent
                width: 4; height: 4; radius: 2
                color: Theme.porcelain
                opacity: backend.state === "listening" || backend.state === "speaking" ? 1 : 0.35
                Behavior on opacity { NumberAnimation { duration: Theme.page } }
            }
        }
        ReiText {
            Layout.alignment: Qt.AlignVCenter
            role: "bodyStrong"
            text: "Rei"
        }
    }

    // Page links: centred in the window, or after the wordmark when narrow
    Row {
        id: links
        anchors.verticalCenter: parent.verticalCenter
        x: root.narrow ? brand.x + brand.width + Theme.s24
                       : Math.round((root.width - width) / 2)
        spacing: 0
        Repeater {
            model: root.pages
            NavLink {
                required property int index
                required property var modelData
                text: modelData.name
                active: root.currentPage === index
                shortcutHint: "Ctrl+" + (index + 1)
                onClicked: root.pageSelected(index)
            }
        }
    }

    RowLayout {
        anchors.right: parent.right
        anchors.rightMargin: Theme.s16
        anchors.verticalCenter: parent.verticalCenter
        spacing: Theme.s8
        NowPlayingCapsule {
            Layout.alignment: Qt.AlignVCenter
            // Never let the title push the bar into the page links
            maxTitleWidth: Math.max(60, Math.min(180, root.width - (links.x + links.width) - 260))
        }
        PrivacyModeButton {
            Layout.alignment: Qt.AlignVCenter
            compact: root.width < 960
        }
    }
}

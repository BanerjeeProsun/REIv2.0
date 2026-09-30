import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

// Shared page frame. Title, subtitle and content live in ONE centred column,
// so every header and the content under it start on the same left axis, and
// the column resizes with the window (never wider than Theme.pageMaxWidth).
Item {
    id: root
    property string title: ""
    property string subtitle: ""
    default property alias content: body.data
    property alias actions: actionRow.data

    ScrollView {
        id: scroller
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: column.implicitHeight + Theme.pageMarginTop + Theme.s40
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: ThinScrollBar {
            parent: scroller
            x: scroller.width - width - 4
            y: scroller.topPadding
            height: scroller.availableHeight
        }

        ColumnLayout {
            id: column
            width: Math.min(scroller.availableWidth - 2 * Theme.pageMarginX, Theme.pageMaxWidth)
            x: Math.round((scroller.availableWidth - width) / 2)
            y: Theme.pageMarginTop
            spacing: Theme.s32

            // HEADER
            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s16

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignBottom
                    spacing: Theme.s8
                    Text {
                        Layout.fillWidth: true
                        text: root.title
                        color: Theme.textPrimary
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.sizeHeadingLg
                        font.weight: Font.DemiBold
                        font.letterSpacing: Theme.tracking(Theme.sizeHeadingLg)
                        elide: Text.ElideRight
                    }
                    Text {
                        visible: root.subtitle !== ""
                        Layout.fillWidth: true
                        text: root.subtitle
                        color: Theme.textSecondary
                        font.family: Theme.fontText
                        font.pixelSize: Theme.sizeBody
                        wrapMode: Text.WordWrap
                    }
                }

                RowLayout {
                    id: actionRow
                    Layout.alignment: Qt.AlignBottom
                    spacing: Theme.s8
                }
            }

            // CONTENT
            ColumnLayout {
                id: body
                Layout.fillWidth: true
                spacing: Theme.s16
            }
        }
    }
}

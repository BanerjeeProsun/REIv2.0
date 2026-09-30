import QtQuick
import QtQuick.Layouts
import ".."

// Small uppercase label that introduces a group of cards.
Text {
    Layout.fillWidth: true
    Layout.topMargin: Theme.s16
    color: Theme.textMuted
    font.family: Theme.fontText
    font.pixelSize: Theme.sizeCaption
    font.weight: Font.DemiBold
    font.capitalization: Font.AllUppercase
    font.letterSpacing: 1.2
}

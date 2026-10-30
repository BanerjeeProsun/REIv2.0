import QtQuick
import QtQuick.Layouts
import ".."

// Group heading above a set of cards (DESIGN.md product label, 19px/600).
ReiText {
    Layout.fillWidth: true
    Layout.topMargin: Theme.s16
    role: "productLabel"
    color: Theme.porcelain
}

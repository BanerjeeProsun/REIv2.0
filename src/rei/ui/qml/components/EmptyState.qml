import QtQuick
import QtQuick.Layouts
import ".."

// Centred placeholder for a page with nothing to show yet.
SurfaceCard {
    id: root
    property url iconSource
    property string title: ""
    property string body: ""
    property string marker: ""   // optional text-only release marker ("Coming soon")
    padding: Theme.s48

    ColumnLayout {
        Layout.fillWidth: true
        spacing: Theme.s8
        Icon {
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: Theme.s8
            source: root.iconSource
            size: 28
            color: Theme.ash
        }
        ReiText {
            Layout.alignment: Qt.AlignHCenter
            visible: root.marker !== ""
            role: "caption"
            text: root.marker
            color: Theme.copperNew
        }
        ReiText {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            role: "productLabel"
            text: root.title
            wrapMode: Text.WordWrap
        }
        ReiText {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            role: "body"
            text: root.body
            color: Theme.ash
            wrapMode: Text.WordWrap
        }
    }
}

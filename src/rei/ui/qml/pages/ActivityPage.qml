import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    title: "Activity"
    subtitle: "A live, auditable record of every action Rei takes."

    SurfaceCard {
        padding: 40
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8
            Icon {
                Layout.alignment: Qt.AlignHCenter
                source: Qt.resolvedUrl("../icons/activity.svg")
                size: 28
                color: Theme.textMuted
            }
            Text {
                Layout.fillWidth: true
                Layout.topMargin: 8
                horizontalAlignment: Text.AlignHCenter
                text: "The activity stream is coming soon"
                color: Theme.textPrimary
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.sizeSubheading
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: "Every decision, confirmation and action will be listed here, straight from the audit log."
                color: Theme.textSecondary
                font.family: Theme.fontText
                font.pixelSize: Theme.sizeBodySm
                wrapMode: Text.WordWrap
            }
        }
    }
}

import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

PageScaffold {
    title: "Activity"
    subtitle: "A live, auditable record of every action Rei takes."

    EmptyState {
        iconSource: Qt.resolvedUrl("../icons/activity.svg")
        marker: "Coming soon"
        title: "The activity stream"
        body: "Every decision, confirmation and action will be listed here, straight from the audit log."
    }
}

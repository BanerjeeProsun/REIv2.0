import QtQuick
import QtQuick.Controls.impl

// Tintable SVG icon. The source SVGs have a baked-in stroke colour, so we
// recolour them to follow hover/active states.
IconImage {
    property int size: 18
    sourceSize.width: size
    sourceSize.height: size
    width: size
    height: size
    fillMode: Image.PreserveAspectFit
    Behavior on color { ColorAnimation { duration: 120 } }
}

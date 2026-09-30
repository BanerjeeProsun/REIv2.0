pragma Singleton
import QtQuick

// Design tokens from design/DESIGN.md (Superlist-inspired):
// warm aubergine surfaces, one coral ember accent, 20px cards, pill controls.
QtObject {
    // Surfaces (dark stack: recessed -> canvas -> elevated)
    readonly property color recessed: "#12121b"
    readonly property color canvas: "#181824"
    readonly property color elevated: "#26253b"
    readonly property color elevatedHover: "#302f4a"
    readonly property color hairline: Qt.rgba(247 / 255, 247 / 255, 1.0, 0.07)
    readonly property color hairlineStrong: Qt.rgba(247 / 255, 247 / 255, 1.0, 0.14)

    // Text. White is for headings; prose uses the softer neutrals.
    readonly property color textPrimary: "#ffffff"
    readonly property color textBody: "#c4c4c8"
    readonly property color textSecondary: "#8e8da0"
    readonly property color textMuted: "#696f81"

    // The single accent. Used surgically: active nav, primary CTA, AI dot, orb.
    readonly property color coral: "#ff4a36"
    readonly property color coralHover: "#ff634f"
    readonly property color coralPressed: "#e63e2b"
    function coralAlpha(a) { return Qt.rgba(1.0, 74 / 255, 54 / 255, a) }

    // Typography: Segoe UI Variable is the native stand-in for Haffer / Inter
    readonly property string fontDisplay: "Segoe UI Variable Display"
    readonly property string fontText: "Segoe UI Variable Text"
    readonly property string fontMono: "Cascadia Mono"

    readonly property int sizeCaption: 12
    readonly property int sizeBodySm: 14
    readonly property int sizeBody: 15
    readonly property int sizeSubheading: 18
    readonly property int sizeHeadingSm: 24
    readonly property int sizeHeading: 30
    readonly property int sizeHeadingLg: 44

    // Tight editorial tracking: -0.02em
    function tracking(size) { return -0.02 * size }

    // Spacing scale
    readonly property int s4: 4
    readonly property int s8: 8
    readonly property int s12: 12
    readonly property int s16: 16
    readonly property int s20: 20
    readonly property int s24: 24
    readonly property int s32: 32
    readonly property int s40: 40

    // Page geometry: every page uses the same column, so headers and content share one axis
    readonly property int pageMarginX: 56
    readonly property int pageMarginTop: 48
    readonly property int pageMaxWidth: 880
    readonly property int sidebarWidth: 232
    readonly property int cardPadding: 24

    // Radii
    readonly property int radiusCard: 20
    readonly property int radiusControl: 10
    readonly property int radiusInput: 8
    readonly property int radiusPill: 100

    // Motion: snappy, never sluggish
    readonly property int fast: 120
    readonly property int page: 150
    readonly property int exit: 90
}

pragma Singleton
import QtQuick

// Design tokens from design/DESIGN.md ("Midnight hardware gallery"):
// a black stage, charcoal panels, Porcelain/Ash type, 1px keylines instead of
// shadows, and Apple Blue reserved for primary actions and focus.
// Every colour in the UI comes from here.
QtObject {
    // Surfaces (level 0 -> 2)
    readonly property color obsidian: "#000000"   // canvas, stage, tiles
    readonly property color graphite: "#0e0e0e"   // chrome, control tracks
    readonly property color carbon: "#1d1d1f"     // panels, cards, dialogs
    readonly property color carbonHover: "#232326"
    readonly property color steel: "#333336"      // keylines, translucent fills
    readonly property color slate: "#6e6e73"      // input/outline borders
    readonly property color keyline: "#282828"    // bar edge (shadow-subtle)
    readonly property color keylineStrong: "#6e6e73" // outlined controls (shadow-subtle-2)
    readonly property color capsule: Qt.rgba(66 / 255, 66 / 255, 69 / 255, 0.72)
    readonly property color capsuleHover: Qt.rgba(86 / 255, 86 / 255, 90 / 255, 0.8)
    readonly property color fieldFill: Qt.rgba(1, 1, 1, 0.04)
    readonly property color fieldFillHover: Qt.rgba(1, 1, 1, 0.07)
    readonly property color hoverFill: Qt.rgba(1, 1, 1, 0.06)
    readonly property color scrim: Qt.rgba(0, 0, 0, 0.72)

    // Text
    readonly property color porcelain: "#f5f5f7"  // primary text on dark
    readonly property color ash: "#86868b"        // muted copy, metadata
    readonly property color white: "#ffffff"
    readonly property color navInk: Qt.rgba(1, 1, 1, 0.8)

    // Accents, used narrowly
    readonly property color appleBlue: "#0071e3"  // primary actions + focus only
    readonly property color appleBlueHover: "#0077ed"
    readonly property color appleBluePressed: "#006edb"
    readonly property color electricLink: "#2997ff" // links on dark
    readonly property color copperNew: "#b64400"  // text-only "New"/"Coming soon"
    // DESIGN.md has no error role (and forbids Copper for errors); this one
    // extension marks errors and high-risk actions only.
    readonly property color alert: "#ff453a"
    function alpha(c, a) { return Qt.rgba(c.r, c.g, c.b, a) }

    // Typography. Segoe UI Variable stands in for SF Pro Display/Text.
    readonly property string fontDisplay: "Segoe UI Variable Display"
    readonly property string fontText: "Segoe UI Variable Text"
    readonly property string fontMono: "Cascadia Mono"

    // Type scale (size px, weight, tracking px, line height, display family?)
    readonly property var type: ({
        "utilityNav":   { size: 12, weight: 400, tracking: -0.12,  lh: 1.33, display: false },
        "caption":      { size: 12, weight: 600, tracking: -0.12,  lh: 1.33, display: false },
        "body":         { size: 14, weight: 400, tracking: -0.224, lh: 1.29, display: false },
        "bodyStrong":   { size: 14, weight: 600, tracking: -0.224, lh: 1.29, display: false },
        "sectionNav":   { size: 17, weight: 500, tracking: -0.374, lh: 1.47, display: false },
        "reading":      { size: 17, weight: 400, tracking: -0.374, lh: 1.47, display: false },
        "productLabel": { size: 19, weight: 600, tracking: 0.228,  lh: 1.21, display: true },
        "featureStat":  { size: 28, weight: 600, tracking: 0.196,  lh: 1.0,  display: true },
        "heroName":     { size: 32, weight: 600, tracking: 0.128,  lh: 1.13, display: true },
        "headline":     { size: 48, weight: 600, tracking: -0.24,  lh: 1.08, display: true },
        "display":      { size: 56, weight: 600, tracking: -0.84,  lh: 1.07, display: true },
        "displayLg":    { size: 80, weight: 600, tracking: -1.2,   lh: 1.05, display: true }
    })

    // Spacing scale
    readonly property int s4: 4
    readonly property int s6: 6
    readonly property int s7: 7
    readonly property int s8: 8
    readonly property int s10: 10
    readonly property int s12: 12
    readonly property int s14: 14
    readonly property int s16: 16
    readonly property int s20: 20
    readonly property int s24: 24
    readonly property int s28: 28
    readonly property int s32: 32
    readonly property int s48: 48
    readonly property int sectionGap: 24
    readonly property int elementGap: 4
    readonly property int cardPadding: 24

    // Geometry
    readonly property int topBarHeight: 44
    readonly property int pageMarginX: 48
    readonly property int pageMarginTop: 48
    readonly property int pageMaxWidth: 980
    readonly property int chatMaxWidth: 760

    // Radii (pills, buttons and inputs are fully round: height / 2)
    readonly property int radiusCard: 28
    readonly property int radiusNav: 20
    readonly property int radiusLink: 10
    readonly property int radiusCompact: 36
    readonly property int radiusKey: 6

    // Motion: quick and quiet
    readonly property int fast: 120
    readonly property int page: 150
    readonly property int exit: 90
}

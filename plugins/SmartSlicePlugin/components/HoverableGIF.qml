import QtQuick 2.4

import UM 1.2 as UM

import SmartSlice 1.0  as SmartSlice

Item {
    id: base

    height: mouse.height

    property alias source: gif.source
    property alias playing: gif.playing
    property alias paused: gif.paused
    property alias framCount: gif.frameCount
    property alias currentFrame: gif.currentFrame

    property alias tooltipTarget: tooltip.target
    property alias tooltipLocation: tooltip.location
    property alias tooltipHeader: tooltip.header
    property alias tooltipDescription: tooltip.description

    signal entered()
    signal exited()
    signal clicked()

    MouseArea {
        id: mouse

        width: parent.width
        height: gif.height

        hoverEnabled: true

        cursorShape: Qt.PointingHandCursor

        onEntered: {
            tooltip.show()
            base.entered()
        }
        onExited: {
            tooltip.hide()
            base.exited()
        }
        onClicked: {
            base.clicked()
        }

        AnimatedImage {
            id: gif

            width: parent.width

            fillMode: Image.PreserveAspectFit
            mipmap: true
            source: base.source
        }
    }

    SmartSlice.SmartSliceTooltip {
        id: tooltip
    }
}

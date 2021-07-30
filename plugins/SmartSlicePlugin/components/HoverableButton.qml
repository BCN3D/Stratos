import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM

import SmartSlice 1.0  as SmartSlice

Item {
    id: base

    property alias hoverEnabled: button.hoverEnabled
    property alias color: button.color
    property alias hoverColor: button.hoverColor
    property alias backgroundColor: button.backgroundColor
    property alias hoverBackgroundColor: button.hoverBackgroundColor
    property alias iconSource: button.iconSource
    property alias iconMargin: button.iconMargin
    property alias hovered: button.hovered
    property alias buttonOpacity: button.opacity

    property alias tooltipTarget: tooltip.target
    property alias tooltipLocation: tooltip.location
    property alias tooltipHeader: tooltip.header
    property alias tooltipDescription: tooltip.description

    signal entered()
    signal exited()
    signal clicked()

    UM.SimpleButton {
        id: button
        visible: base.visible
        enabled: base.enabled

        anchors.fill: parent

        onEntered: {
            base.entered()
            tooltip.show()
        }

        onExited: {
            base.exited()
            tooltip.hide()
        }

        onClicked: {
            base.clicked()
        }
    }

    SmartSlice.SmartSliceTooltip {
        id: tooltip
    }
}

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import SmartSlice 1.0  as SmartSlice

Item {
    id: base

    height: UM.Theme.getSize("section").height
    width: parent.width

    property alias model: comboBox.model
    property alias currentIndex: comboBox.currentIndex
    property alias highlightedIndex: comboBox.highlightedIndex

    property alias tooltipTarget: tooltip.target
    property alias tooltipLocation: tooltip.location

    property var tooltipHeaders
    property var tooltipDescriptions

    signal activated()
    signal highlighted()
    signal entered()
    signal exited()

    MouseArea {
        id: mouse

        anchors.fill: parent

        acceptedButtons: Qt.RightButton
        hoverEnabled: true

        onEntered: {
            tooltip.header = base.tooltipHeaders[currentIndex]
            tooltip.description = base.tooltipDescriptions[currentIndex]
            tooltip.show();
            base.entered();
        }
        onExited: {
            tooltip.hide();
            base.exited();
        }

        Cura.ComboBox {
            id: comboBox

            height: parent.height
            width: parent.width

            hoverEnabled: true

            textRole: "key"

            onActivated: {
                base.activated();
                tooltip.hide();
            }

            onHighlighted: {
                base.highlighted();
                tooltip.header = base.tooltipHeaders[highlightedIndex]
                tooltip.description = base.tooltipDescriptions[highlightedIndex]
                tooltip.show();
            }
        }
    }

    SmartSlice.SmartSliceTooltip {
        id: tooltip
    }
}

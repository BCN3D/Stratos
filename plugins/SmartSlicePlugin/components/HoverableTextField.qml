import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM

import SmartSlice 1.0  as SmartSlice

Item {
    id: base

    height: UM.Theme.getSize("section").height

    property alias hovered: mouse.containsMouse
    property alias text: field.text
    property alias validator: field.validator
    property alias inputMethodHints: field.inputMethodHints
    property alias unit: field.unit
    property alias readOnly: field.readOnly

    property alias tooltipTarget: tooltip.target
    property alias tooltipLocation: tooltip.location
    property alias tooltipHeader: tooltip.header
    property alias tooltipDescription: tooltip.description

    signal entered()
    signal exited()
    signal editingFinished()

    MouseArea {
        id: mouse

        anchors.fill: parent

        acceptedButtons: Qt.RightButton
        hoverEnabled: true
        onEntered: {
            tooltip.show()
            base.entered()
        }
        onExited: {
            tooltip.hide()
            base.exited()
        }

        TextField {
            id: field
            style: UM.Theme.styles.text_field
            anchors.fill: parent

            onEditingFinished: base.editingFinished()

            property string unit
        }
    }

    SmartSlice.SmartSliceTooltip {
        id: tooltip
    }
}

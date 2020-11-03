// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.0 as Cura

// We show a nice overlay on the 3D viewer when the current output device has no monitor view
Rectangle
{
    id: viewportOverlay

    property bool isConnected: Cura.MachineManager.activeMachineHasNetworkConnection || Cura.MachineManager.activeMachineHasCloudConnection
    property bool isNetworkConfigurable:
    {
        if(Cura.MachineManager.activeMachine === null)
        {
            return false
        }
        return Cura.MachineManager.activeMachine.supportsNetworkConnection
    }

    property bool isNetworkConfigured:
    {
        // Readability:
        var connectedTypes = [2, 3];
        var types = Cura.MachineManager.activeMachine.configuredConnectionTypes

        // Check if configured connection types includes either 2 or 3 (LAN or cloud)
        for (var i = 0; i < types.length; i++)
        {
            if (connectedTypes.indexOf(types[i]) >= 0)
            {
                return true
            }
        }
        return false
    }

    color: UM.Theme.getColor("viewport_overlay")
    anchors.fill: parent

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    // This mouse area is to prevent mouse clicks to be passed onto the scene.
    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onWheel: wheel.accepted = true
    }

    // Disable dropping files into Cura when the monitor page is active
    DropArea
    {
        anchors.fill: parent
    }

    // CASE 1: CAN MONITOR & CONNECTED
    Loader
    {
        id: monitorViewComponent

        anchors.fill: parent

        height: parent.height

        property real maximumWidth: parent.width
        property real maximumHeight: parent.height

        sourceComponent: Cura.MachineManager.printerOutputDevices.length > 0 ? Cura.MachineManager.printerOutputDevices[0].monitorItem : null
    }

    // CASE 2 & 3: Empty states
    Column
    {
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("monitor_empty_state_offset").height
            horizontalCenter: parent.horizontalCenter
        }
        width: UM.Theme.getSize("monitor_empty_state_size").width
        spacing: UM.Theme.getSize("default_margin").height
        visible: monitorViewComponent.sourceComponent == null

        // CASE 2: CAN MONITOR & NOT CONNECTED
        Label
        {
            anchors
            {
                horizontalCenter: parent.horizontalCenter
            }
            visible: isNetworkConfigured && !isConnected
            text: catalog.i18nc("@info", "Please make sure your printer has a connection:\n- Check if the printer is turned on.\n- Check if the printer is connected to the network.\n- Check if you are signed in to discover cloud-connected printers.")
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("monitor_text_primary")
            wrapMode: Text.WordWrap
            lineHeight: UM.Theme.getSize("monitor_text_line_large").height
            lineHeightMode: Text.FixedHeight
            width: contentWidth
        }

        Label
        {
            id: noNetworkLabel
            anchors
            {
                horizontalCenter: parent.horizontalCenter
            }
            visible: !isNetworkConfigured && isNetworkConfigurable
            text: catalog.i18nc("@info", "Please connect your printer to the network.")
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("monitor_text_primary")
            wrapMode: Text.WordWrap
            width: contentWidth
            lineHeight: UM.Theme.getSize("monitor_text_line_large").height
            lineHeightMode: Text.FixedHeight
        }
        Item
        {
            anchors
            {
                left: noNetworkLabel.left
            }
            visible: !isNetworkConfigured && isNetworkConfigurable
            height: UM.Theme.getSize("monitor_text_line").height
            width: childrenRect.width

            UM.RecolorImage
            {
                id: externalLinkIcon
                anchors.verticalCenter: parent.verticalCenter
                color: UM.Theme.getColor("text_link")
                source: UM.Theme.getIcon("external_link")
                width: UM.Theme.getSize("monitor_external_link_icon").width
                height: UM.Theme.getSize("monitor_external_link_icon").height
            }
            Label
            {
                id: manageQueueText
                anchors
                {
                    left: externalLinkIcon.right
                    leftMargin: UM.Theme.getSize("narrow_margin").width
                    verticalCenter: externalLinkIcon.verticalCenter
                }
                color: UM.Theme.getColor("text_link")
                font: UM.Theme.getFont("medium")
                text: catalog.i18nc("@label link to technical assistance", "View user manuals online")
                renderType: Text.NativeRendering
            }
            MouseArea
            {
                anchors.fill: parent
                hoverEnabled: true
                onClicked: Qt.openUrlExternally("https://ultimaker.com/en/resources/manuals/ultimaker-3d-printers")
                onEntered: manageQueueText.font.underline = true
                onExited: manageQueueText.font.underline = false
            }
        }
    }
}

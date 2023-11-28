// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura


// This element contains all the elements the user needs to create a printjob from the
// model(s) that is(are) on the buildplate. Mainly the button to start/stop the slicing
// process and a progress bar to see the progress of the process.
Column
{
    id: widget

    spacing: UM.Theme.getSize("thin_margin").height

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    property real progress: UM.Backend.progress
    property int backendState: UM.Backend.state
    // As the collection of settings to send to the engine might take some time, we have an extra value to indicate
    // That the user pressed the button but it's still waiting for the backend to acknowledge that it got it.
    property bool waitingForSliceToStart: false
    onBackendStateChanged: waitingForSliceToStart = false

    function sliceOrStopSlicing()
    {
        if (widget.backendState == UM.Backend.NotStarted)
        {
            widget.waitingForSliceToStart = true
            CuraApplication.backend.forceSlice()
        }
        else
        {
            widget.waitingForSliceToStart = false
            CuraApplication.backend.stopSlicing()
        }
    }

    UM.Label
    {
        id: autoSlicingLabel
        width: parent.width
        visible: progressBar.visible

        text: catalog.i18nc("@label:PrintjobStatus", "Slicing...")
    }
    Item
    {
        id: unableToSliceMessage
        width: parent.width
        visible: widget.backendState == UM.Backend.Error

        height: warningIcon.height
        UM.StatusIcon
        {
            id: warningIcon
            anchors.verticalCenter: parent.verticalCenter
            width: visible ? UM.Theme.getSize("section_icon").width : 0
            height: width
            status: UM.StatusIcon.Status.WARNING
        }
        UM.Label
        {
            id: label
            anchors.left: warningIcon.right
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@label:PrintjobStatus", "Unable to slice")
            wrapMode: Text.WordWrap
        }
    }

    // Progress bar, only visible when the backend is in the process of slice the printjob
    UM.ProgressBar
    {
        id: progressBar
        width: parent.width
        height: UM.Theme.getSize("progressbar").height
        value: progress
        indeterminate: widget.backendState == UM.Backend.NotStarted
        visible: (widget.backendState == UM.Backend.Processing || (prepareButtons.autoSlice && widget.backendState == UM.Backend.NotStarted))
    }

    Item
    {
        id: prepareButtons
        // Get the current value from the preferences
        property bool autoSlice: UM.Preferences.getValue("general/auto_slice")
        // Disable the slice process when

        width: parent.width
        height: UM.Theme.getSize("action_button").height
        visible: !autoSlice
        Cura.PrimaryButton
        {
            id: sliceButton
            fixedWidthMode: true

            height: parent.height

            anchors.right: parent.right
            anchors.left: parent.left

            text: widget.waitingForSliceToStart ? catalog.i18nc("@button", "Processing"): catalog.i18nc("@button", "Slice")
            tooltip: catalog.i18nc("@label", "Start the slicing process")
            hoverEnabled: !widget.waitingForSliceToStart
            enabled: widget.backendState != UM.Backend.Error && !widget.waitingForSliceToStart
            visible: widget.backendState == UM.Backend.NotStarted || widget.backendState == UM.Backend.Error
            onClicked: {
                sliceOrStopSlicing()
            }
        }

        Cura.SecondaryButton
        {
            id: cancelButton
            fixedWidthMode: true
            height: parent.height
            anchors.left: parent.left

            anchors.right: parent.right
            text: catalog.i18nc("@button", "Cancel")
            enabled: sliceButton.enabled
            visible: !sliceButton.visible
            onClicked: {
                sliceOrStopSlicing()
            }
        }
    }


    // React when the user changes the preference of having the auto slice enabled
    Connections
    {
        target: UM.Preferences
        function onPreferenceChanged(preference)
        {
            if (preference !== "general/auto_slice")
            {
                return;
            }

            var autoSlice = UM.Preferences.getValue("general/auto_slice")
            if(prepareButtons.autoSlice != autoSlice)
            {
                prepareButtons.autoSlice = autoSlice
                if(autoSlice)
                {
                    CuraApplication.backend.forceSlice()
                }
            }
        }
    }

    // Shortcut for "slice/stop"
    Action
    {
        shortcut: "Ctrl+P"
        onTriggered:
        {
            if (sliceButton.enabled)
            {
                sliceOrStopSlicing()
            }
        }
    }
}

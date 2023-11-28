// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.5 as Cura


//
// This component contains the content for the 'by IP' page of the "Add New Printer" flow of the on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    id: addPrinterByIpScreen

    // If there's a manual address resolve request in progress.
    property bool hasRequestInProgress: CuraApplication.getDiscoveredPrintersModel().hasManualDeviceRequestInProgress
    // Indicates if a request has finished.
    property bool hasRequestFinished: false
    property string currentRequestAddress: ""

    property var discoveredPrinter: null
    property bool isPrinterDiscovered: discoveredPrinter != null
    // A printer can only be added if it doesn't have an unknown type and it's the host of a group.
    property bool canAddPrinter: isPrinterDiscovered && !discoveredPrinter.isUnknownMachineType && discoveredPrinter.isHostOfGroup

    // For validating IP address
    property var networkingUtil: Cura.NetworkingUtil {}

    // CURA-6483
    // For a manually added UM printer, the UM3OutputDevicePlugin will first create a LegacyUM device for it. Later,
    // when it gets more info from the printer, it will first REMOVE the LegacyUM device and then add a ClusterUM device.
    // The Add-by-IP page needs to make sure that the user do not add an unknown printer or a printer that's not the
    // host of a group. Because of the device list change, this page needs to react upon DiscoveredPrintersChanged so
    // it has the correct information.
    Connections
    {
        target: CuraApplication.getDiscoveredPrintersModel()
        function onDiscoveredPrintersChanged()
        {
            if (hasRequestFinished && currentRequestAddress)
            {
                var printer = CuraApplication.getDiscoveredPrintersModel().discoveredPrintersByAddress[currentRequestAddress]
                printer = printer ? printer : null
                discoveredPrinter = printer
            }
        }
    }

    // Make sure to cancel the current request when this page closes.
    onVisibleChanged:
    {
        if (!visible)
        {
            CuraApplication.getDiscoveredPrintersModel().cancelCurrentManualDeviceRequest()
        }
    }

    UM.Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Add printer by IP address")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
    }

    Item
    {
        anchors.top: titleLabel.bottom
        anchors.bottom: connectButton.top
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        anchors.right: parent.right

        Item
        {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: UM.Theme.getSize("default_margin").width

            UM.Label
            {
                id: explainLabel
                height: contentHeight
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                text: catalog.i18nc("@label", "Enter the IP address of your printer on the network.")
            }

            Item
            {
                id: userInputFields
                height: childrenRect.height
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: explainLabel.bottom
                anchors.topMargin: UM.Theme.getSize("default_margin").width

                Cura.TextField
                {
                    id: hostnameField
                    width: (parent.width / 2) | 0
                    height: addPrinterButton.height
                    anchors.verticalCenter: addPrinterButton.verticalCenter
                    anchors.left: parent.left

                    signal invalidInputDetected()

                    onInvalidInputDetected: invalidInputLabel.visible = true

                    validator: RegularExpressionValidator
                    {
                        regularExpression: /([a-fA-F0-9.:]+)?/
                    }

                    onTextEdited: invalidInputLabel.visible = false

                    placeholderText: catalog.i18nc("@text", "Enter your printer's IP address.")

                    enabled: { ! (addPrinterByIpScreen.hasRequestInProgress || addPrinterByIpScreen.isPrinterDiscovered) }
                    onAccepted: addPrinterButton.clicked()
                }

                UM.Label
                {
                    id: invalidInputLabel
                    anchors.top: hostnameField.bottom
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                    anchors.left: parent.left
                    visible: false
                    text: catalog.i18nc("@text", "Please enter a valid IP address.")
                }

                Cura.SecondaryButton
                {
                    id: addPrinterButton
                    anchors.top: parent.top
                    anchors.left: hostnameField.right
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    text: catalog.i18nc("@button", "Add")
                    enabled: !addPrinterByIpScreen.hasRequestInProgress && !addPrinterByIpScreen.isPrinterDiscovered && (hostnameField.state != "invalid" && hostnameField.text != "")
                    onClicked:
                    {
                        addPrinterByIpScreen.hasRequestFinished = false //In case it's pressed multiple times.
                        const address = hostnameField.text
                        if (!networkingUtil.isValidIP(address))
                        {
                            hostnameField.invalidInputDetected()
                            return
                        }

                        // This address is already in the discovered printer model, no need to add a manual discovery.
                        if (CuraApplication.getDiscoveredPrintersModel().discoveredPrintersByAddress[address])
                        {
                            addPrinterByIpScreen.discoveredPrinter = CuraApplication.getDiscoveredPrintersModel().discoveredPrintersByAddress[address]
                            addPrinterByIpScreen.hasRequestFinished = true
                            return
                        }

                        addPrinterByIpScreen.currentRequestAddress = address
                        CuraApplication.getDiscoveredPrintersModel().checkManualDevice(address)
                    }
                    busy: addPrinterByIpScreen.hasRequestInProgress
                }
            }

            Item
            {
                width: parent.width
                anchors.top: userInputFields.bottom
                anchors.margins: UM.Theme.getSize("default_margin").width

                UM.Label
                {
                    id: waitResponseLabel
                    anchors.top: parent.top
                    anchors.margins: UM.Theme.getSize("default_margin").width

                    visible: addPrinterByIpScreen.hasRequestInProgress || (addPrinterByIpScreen.hasRequestFinished && !addPrinterByIpScreen.isPrinterDiscovered)
                    textFormat: Text.RichText
                    text:
                    {
                        if (addPrinterByIpScreen.hasRequestFinished)
                        {
                            return catalog.i18nc("@label", "Could not connect to device.") + "<br /><br /><a href=\"https://ultimaker.com/in/cura/troubleshooting/network?utm_source=cura&utm_medium=software&utm_campaign=add-network-printer-error\">"
                                + catalog.i18nc("@label", "Can't connect to your UltiMaker printer?") + "</a>";
                        }
                        else
                        {
                            return catalog.i18nc("@label", "The printer at this address has not responded yet.") + "<br /><br /><a href=\"https://ultimaker.com/in/cura/troubleshooting/network?utm_source=cura&utm_medium=software&utm_campaign=add-network-printer-error\">"
                                + catalog.i18nc("@label", "Can't connect to your UltiMaker printer?") + "</a>";
                        }
                    }
                    onLinkActivated: Qt.openUrlExternally(link)
                }

                Item
                {
                    id: printerInfoLabels
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: UM.Theme.getSize("default_margin").width

                    visible: addPrinterByIpScreen.isPrinterDiscovered

                    UM.Label
                    {
                        id: printerNameLabel
                        anchors.top: parent.top
                        font: UM.Theme.getFont("large")
                        text: !addPrinterByIpScreen.isPrinterDiscovered ? "???" : addPrinterByIpScreen.discoveredPrinter.name
                    }

                    UM.Label
                    {
                        id: printerCannotBeAddedLabel
                        width: parent.width
                        anchors.top: printerNameLabel.bottom
                        anchors.topMargin: UM.Theme.getSize("default_margin").height
                        text: catalog.i18nc("@label", "This printer cannot be added because it's an unknown printer or it's not the host of a group.")
                        visible: addPrinterByIpScreen.hasRequestFinished && !addPrinterByIpScreen.canAddPrinter
                        font: UM.Theme.getFont("default_bold")
                        wrapMode: Text.WordWrap
                    }

                    GridLayout
                    {
                        id: printerInfoGrid
                        anchors.top: printerCannotBeAddedLabel ? printerCannotBeAddedLabel.bottom : printerNameLabel.bottom
                        anchors.margins: UM.Theme.getSize("default_margin").width
                        columns: 2
                        columnSpacing: UM.Theme.getSize("default_margin").width

                        UM.Label
                        {
                            text: catalog.i18nc("@label", "Type")
                        }
                        UM.Label
                        {
                            id: typeText
                            text: !addPrinterByIpScreen.isPrinterDiscovered ? "?" : addPrinterByIpScreen.discoveredPrinter.readableMachineType
                        }
                        UM.Label
                        {
                            text: catalog.i18nc("@label", "Firmware version")
                        }
                        UM.Label
                        {
                            id: firmwareText
                            text: !addPrinterByIpScreen.isPrinterDiscovered ? "0.0.0.0" : addPrinterByIpScreen.discoveredPrinter.device.getProperty("firmware_version")
                        }

                        UM.Label
                        {
                            text: catalog.i18nc("@label", "Address")
                        }
                        UM.Label
                        {
                            id: addressText
                            text: !addPrinterByIpScreen.isPrinterDiscovered ? "0.0.0.0" : addPrinterByIpScreen.discoveredPrinter.address
                        }
                    }

                    Connections
                    {
                        target: CuraApplication.getDiscoveredPrintersModel()
                        function onManualDeviceRequestFinished(success)
                        {
                            var discovered_printers_model = CuraApplication.getDiscoveredPrintersModel()
                            var printer = discovered_printers_model.discoveredPrintersByAddress[hostnameField.text]
                            if (printer)
                            {
                                addPrinterByIpScreen.discoveredPrinter = printer
                            }
                            addPrinterByIpScreen.hasRequestFinished = true
                        }
                    }
                }
            }
        }
    }

    Cura.SecondaryButton
    {
        id: backButton
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Back")
        onClicked:
        {
            CuraApplication.getDiscoveredPrintersModel().cancelCurrentManualDeviceRequest()
            base.showPreviousPage()
        }
    }

    Cura.PrimaryButton
    {
        id: connectButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Connect")
        onClicked:
        {
            CuraApplication.getDiscoveredPrintersModel().createMachineFromDiscoveredPrinter(discoveredPrinter)
            base.showNextPage()
        }

        enabled: addPrinterByIpScreen.canAddPrinter
    }
}

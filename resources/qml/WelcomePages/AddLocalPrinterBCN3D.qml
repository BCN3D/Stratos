// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "Add a printer" (network) page of the welcome on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Add a printer")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
        renderType: Text.NativeRendering
    }



    DropDownWidget
    {
        id: addLocalPrinterDropDown

        anchors.top: addNetworkPrinterDropDown.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        contentShown: true  // by default expand the network printer list
        title: catalog.i18nc("@label", "Add a non-networked printer")

        onClicked:
        {
            addNetworkPrinterDropDown.contentShown = !contentShown
        }

        contentComponent: localPrinterListComponent

        Component
        {
            id: localPrinterListComponent

            AddLocalPrinterScrollView
            {
                id: localPrinterView
                property int childrenHeight: backButton.y - addLocalPrinterDropDown.y - UM.Theme.getSize("expandable_component_content_header").height - UM.Theme.getSize("default_margin").height

                onChildrenHeightChanged:
                {
                    addLocalPrinterDropDown.children[1].height = childrenHeight
                }
            }
        }
    }

    // This "Back" button only shows in the "Add Machine" dialog, which has "previous_page_button_text" set to "Cancel"
    Cura.SecondaryButton
    {
        id: backButton
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        visible: base.currentItem.previous_page_button_text ? true : false
        text: base.currentItem.previous_page_button_text ? base.currentItem.previous_page_button_text : ""
        onClicked:
        {
            base.endWizard()
        }
    }

    Cura.PrimaryButton
    {
        id: nextButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        enabled:
        {
            // If the network printer dropdown is expanded, make sure that there is a selected item

                // Printer name cannot be empty
                const localPrinterItem = addLocalPrinterDropDown.contentItem.currentItem
                const isPrinterNameValid = addLocalPrinterDropDown.contentItem.isPrinterNameValid
                return localPrinterItem != null && isPrinterNameValid

        }

        text: base.currentItem.next_page_button_text
        onClicked:
        {
                // Create a local printer
                const localPrinterItem = addLocalPrinterDropDown.contentItem.currentItem
                const printerName = addLocalPrinterDropDown.contentItem.printerName
                if(Cura.MachineManager.addMachine(localPrinterItem.id, printerName))
                {
                    base.showNextPage()
                }

        }
    }
}

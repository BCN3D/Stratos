import QtQuick 2.7
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import QtGraphicalEffects 1.0 // For the dropshadow

Item {
    id: smartSliceMenu

    UM.I18nCatalog {
        id: catalog
        name: "smartslice"
    }

    anchors {
        left: parent.left
        right: parent.right
        leftMargin: UM.Theme.getSize("wide_margin").width
        rightMargin: UM.Theme.getSize("wide_margin").width
    }

    // Item to ensure that all of the buttons are nicely centered.
    Item
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 2 * UM.Theme.getSize("wide_margin").width
        height: parent.height

        RowLayout
        {
            id: itemRow

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            height: parent.height
            spacing: 0

            Cura.ConfigurationMenu {
                id: printerSetup
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: itemRow.width - printSetupSelectorItem.width - 2 * UM.Theme.getSize("default_lining").width
            }

            // Separator line
            Rectangle {
                height: parent.height
                width: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("lining")
            }

            Item
            {
                id: printSetupSelectorItem
                // This is a work around to prevent the printSetupSelector from having to be re-loaded every time
                // a stage switch is done.
                children: [printSetupSelector]
                height: childrenRect.height
                width: childrenRect.width
            }
        }
    }
}

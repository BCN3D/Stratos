// Copyright (c) 2020 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4

import UM 1.4 as UM
import Cura 1.0 as Cura

Item
{
    id: header
    width: parent.width
    height: UM.Theme.getSize("toolbox_header").height
    Row
    {
        id: bar
        spacing: UM.Theme.getSize("default_margin").width
        height: childrenRect.height
        width: childrenRect.width
        anchors
        {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
        }


        ToolboxTabButton
        {
            id: installedTabButton
            text: catalog.i18nc("@title:tab", "Installed")
            active: enableButton()
            enabled: !toolbox.isDownloading
            onClicked: toolbox.viewCategory = "installed"
            width: UM.Theme.getSize("toolbox_header_tab").width + marketplaceNotificationIcon.width - UM.Theme.getSize("default_margin").width

            function enableButton() {

            toolbox.viewCategory = "installed"
            return true
            }

        }


    }

    Cura.NotificationIcon
    {
        id: marketplaceNotificationIcon
        visible: CuraApplication.getPackageManager().packagesWithUpdate.length > 0
        anchors.right: bar.right
        labelText:
        {
            const itemCount = CuraApplication.getPackageManager().packagesWithUpdate.length
            return itemCount > 9 ? "9+" : itemCount
        }
    }




    ToolboxShadow
    {
        anchors.top: bar.bottom
    }
}


// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

import UM 1.2 as UM
import Cura 1.1 as Cura
import ".."


Item
{
    id: base
    width: childrenRect.width
    height: childrenRect.height



    UM.I18nCatalog { id: catalog; name: "cura"}

    Column
    {
        id: items
        anchors.top: parent.top;
        anchors.left: parent.left;

        spacing: UM.Theme.getSize("default_margin").height

        Row
        {
            id: duplicationButtons
            spacing: UM.Theme.getSize("default_margin").width
            Button
            {
                id: duplication
                text: catalog.i18nc("@label", "duplication")
                iconSource: UM.Theme.getIcon("pos_normal");
                property bool needBorder: true
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("duplication")
                 CuraActions.centerSelection();
                }
                style: UM.Theme.styles.tool_button;
                z: 5
            }
            Button
            {
                id: singleT0Button
                text: catalog.i18nc("@label", "singleT0")
                iconSource: UM.Theme.getIcon("pos_normal");
                property bool needBorder: true
                onClicked: {
                 Cura.PrintersManagerService.setPrintMode("singleT0");
                 CuraActions.centerSelection();
                    }
                style: UM.Theme.styles.tool_button;
                z: 4
            }

            Button
            {
                id: singleT1Button
                text: catalog.i18nc("@label", "singleT1")
                iconSource: UM.Theme.getIcon("pos_print_as_support");
                property bool needBorder: true
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("singleT1")
                 CuraActions.centerSelection();
                }
                style: UM.Theme.styles.tool_button;
                z: 3
            }

            Button
            {
                id: dualButton
                text: catalog.i18nc("@label", "Dual")
                iconSource: UM.Theme.getIcon("pos_modify_overlaps");
                property bool needBorder: true
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("dual")
                 CuraActions.centerSelection();
                }
                style: UM.Theme.styles.tool_button;
                z: 2
            }

            Button
            {
                id: mirrorButton
                text:  catalog.i18nc("@label", "Mirror")
                iconSource: UM.Theme.getIcon("pos_modify_dont_support_overlap");
                property bool needBorder: true
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("mirror")
                 CuraActions.centerSelection();
                }
                style: UM.Theme.styles.tool_button;
                z: 1
            }

        }

        Label
        {
            id: printModeLabel
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            height: UM.Theme.getSize("setting").height
            verticalAlignment: Text.AlignVCenter
        }


    }

}


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


    property var extrudersModel: CuraApplication.getExtrudersModel()
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
                id: dualButton
                text: catalog.i18nc("@label", "Dual")
                iconSource: UM.Theme.getIcon("dualicon");
                property bool needBorder: true
                checkable: true
                checked: Cura.PrintersManagerService.getPrintMode() == "dual"
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("dual")
                 CuraActions.setExtruderForSelection(extrudersModel.getItem(0).id)
                }
                style: UM.Theme.styles.tool_button;
                z: 5
            }
             Button
            {
                id: singleT0Button
                text: catalog.i18nc("@label", "Single 1")
                iconSource: UM.Theme.getIcon("single1");
                property bool needBorder: true
                checkable: true
                checked: Cura.PrintersManagerService.getPrintMode() == "singleT0"
                onClicked: {
                 Cura.PrintersManagerService.setPrintMode("singleT0");
                 CuraActions.setExtruderForSelection(extrudersModel.getItem(0).id)
                    }
                style: UM.Theme.styles.tool_button;
                z: 4
            }

            Button
            {
                id: singleT1Button
                text: catalog.i18nc("@label", "Single 2")
                iconSource: UM.Theme.getIcon("single2");
                property bool needBorder: true
                checkable: true
                checked: Cura.PrintersManagerService.getPrintMode() == "singleT1"
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("singleT1")
                 CuraActions.setExtruderForSelection(extrudersModel.getItem(1).id)
                }
                style: UM.Theme.styles.tool_button;
                z: 3
            }
             Button
            {
                id: duplication
                text: catalog.i18nc("@label", "Duplication")
                iconSource: UM.Theme.getIcon("duplicationicon");
                property bool needBorder: true
                checkable: true
                checked: Cura.PrintersManagerService.getPrintMode() == "duplication"
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("duplication")
                 CuraActions.setExtruderForSelection(extrudersModel.getItem(0).id)

                }
                style: UM.Theme.styles.tool_button;
                z: 2
            }
            Button
            {
                id: mirrorButton
                text:  catalog.i18nc("@label", "Mirror")
                iconSource: UM.Theme.getIcon("mirroricon");
                property bool needBorder: true
                checkable: true
                checked: Cura.PrintersManagerService.getPrintMode() == "mirror"
                onClicked:{
                 Cura.PrintersManagerService.setPrintMode("mirror")
                 CuraActions.setExtruderForSelection(extrudersModel.getItem(0).id)

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

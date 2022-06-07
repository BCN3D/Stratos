
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

        Label
        {
            id: panelLabel
            text: catalog.i18nc("@info:tooltip", "Create a volume in which supports are not printed.")
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            height: UM.Theme.getSize("setting").height
            verticalAlignment: Text.AlignVCenter
        }
    }

}

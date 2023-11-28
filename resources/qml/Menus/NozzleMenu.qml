// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.4

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: nozzleMenu
    title: "Nozzle"

    property int extruderIndex: 0

    Cura.NozzleModel
    {
        id: nozzleModel
    }

    Instantiator
    {
        model: nozzleModel

        Cura.MenuItem
        {
            text: model.hotend_name
            checkable: true
            property var activeMachine: Cura.MachineManager.activeMachine
            checked:
            {
                if (activeMachine === null)
                {
                    return false
                }
                var extruder = activeMachine.extruderList[extruderIndex]
                return (extruder === undefined) ? false : (extruder.variant.name == model.hotend_name)
            }
            enabled:
            {
                if (activeMachine === null)
                {
                    return false
                }
                var extruder = activeMachine.extruderList[extruderIndex]
                return (extruder === undefined) ? false : extruder.isEnabled
            }
            onTriggered: Cura.MachineManager.setVariant(nozzleMenu.extruderIndex, model.container_node)
        }

        onObjectAdded: function(index, object) { nozzleMenu.insertItem(index, object) }
        onObjectRemoved: function(index, object) {nozzleMenu.removeItem(object)}
    }

}

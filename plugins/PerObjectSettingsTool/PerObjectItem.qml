// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.TooltipArea
{
    x: model.depth * UM.Theme.getSize("narrow_margin").width
    text: model.description

    width: childrenRect.width
    height: childrenRect.height

    UM.CheckBox
    {
        id: check
        text: definition.label
        checked: addedSettingsModel.getVisible(model.key)

        onClicked:
        {
            addedSettingsModel.setVisible(model.key, checked);
            UM.ActiveTool.forceUpdate();
        }
    }

    // When the user removes settings from the list addedSettingsModel, we need to recheck if the
    // setting is visible or not to show a mark in the CheckBox.
    Connections
    {
        target: addedSettingsModel
        function onVisibleCountChanged()
        {
            check.checked = addedSettingsModel.getVisible(model.key)
        }
    }
}



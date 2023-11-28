// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.7 as Cura


RecommendedSettingSection
{
    id: enableSupportRow

    title: catalog.i18nc("@label", "Support")
    icon: UM.Theme.getIcon("Support")
    enableSectionSwitchVisible: supportEnabled.properties.enabled == "True"
    enableSectionSwitchChecked: supportEnabled.properties.value == "True"
    enableSectionSwitchEnabled: recommendedPrintSetup.settingsEnabled
    tooltipText: catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, these parts would collapse during printing.")

    function onEnableSectionChanged(state)
    {
        supportEnabled.setPropertyValue("value", state)
    }

    property UM.SettingPropertyProvider supportEnabled: UM.SettingPropertyProvider
    {
        id: supportEnabled
        containerStack: Cura.MachineManager.activeStack
        key: "support_enable"
        watchedProperties: [ "value", "enabled", "description" ]
        storeIndex: 0
    }

    contents: [
        RecommendedSettingItem
        {
            Layout.preferredHeight: childrenRect.height
            settingName: catalog.i18nc("@action:label", "Print with")
            tooltipText: catalog.i18nc("@label", "The extruder train to use for printing the support. This is used in multi-extrusion.")
            // Hide this component when there is only one extruder
            enabled: Cura.ExtruderManager.enabledExtruderCount > 1
            visible: Cura.ExtruderManager.enabledExtruderCount > 1
            isCompressed: enableSupportRow.isCompressed || Cura.ExtruderManager.enabledExtruderCount <= 1

            settingControl: Cura.SingleSettingExtruderSelectorBar
            {
                extruderSettingName: "support_extruder_nr"
            }
        }
    ]
}

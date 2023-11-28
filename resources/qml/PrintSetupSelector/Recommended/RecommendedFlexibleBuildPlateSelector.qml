// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.7 as Cura


RecommendedSettingSection
{
    id: enableAdhesionRow

    title: catalog.i18nc("@label", "Flexible Surface")
    icon: UM.Theme.getIcon("Flexible")
    enableSectionSwitchVisible: platformAdhesionType.properties.enabled === "True"
    enableSectionSwitchChecked: platformAdhesionType.properties.value === "True"
    enableSectionSwitchEnabled: recommendedPrintSetup.settingsEnabled
    tooltipText: catalog.i18nc("@label", "Enable printing in Flexible Surface, this will rise up the temperatures for a propper printing.")

    property var curaRecommendedMode: Cura.RecommendedMode {}

    property UM.SettingPropertyProvider platformAdhesionType: UM.SettingPropertyProvider
    {
        containerStack: Cura.MachineManager.activeMachine
        removeUnusedValue: false //Doesn't work with settings that are resolved.
        key: "flexible_bed"
        watchedProperties: [ "value", "resolve", "enabled" ]
        storeIndex: 0
    }

    function onEnableSectionChanged(state)
    {
        curaRecommendedMode.setFlexibleBed(state)
    }
}

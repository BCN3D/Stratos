// Copyright (c) 2023 UltiMaker
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura
import ".."

Flickable
{
    id: recommendedOmegaPrintSetup
    clip: true

    contentHeight: settingsColumn.height
    implicitHeight: settingsColumn.height

    property bool settingsEnabled: Cura.ExtruderManager.activeExtruderStackId || extrudersEnabledCount.properties.value == 1

    property var profile: Cura.APIManager.profile

    function onModeChanged() {}

    ScrollBar.vertical: UM.ScrollBar {
        id: scroll
        anchors
        {
            top: parent.top
            right: parent.right
            bottom: parent.bottom
        }
    }

    boundsBehavior: Flickable.StopAtBounds

    Column
    {
        id: settingsColumn
        padding: UM.Theme.getSize("default_margin").width
        spacing: UM.Theme.getSize("default_margin").height

        width: recommendedPrintSetup.width - 2 * padding - UM.Theme.getSize("thin_margin").width

        // TODO
        property real firstColumnWidth: Math.round(width / 3)

        UM.Label
        {
            text: catalog.i18nc("@label", "Profiles")
            font: UM.Theme.getFont("medium")
        }

        RecommendedQualityProfileSelector
        {
            width: parent.width
            hasQualityOptions: recommendedResolutionSelector.visible && Cura.MachineManager.isActiveQualitySupported
        }

        RecommendedResolutionSelector
        {
            id: recommendedResolutionSelector
            visible : Cura.MachineManager.isActiveQualitySupported
            width: parent.width
        }

        UnsupportedProfileIndication
        {
            width: parent.width
            visible: !recommendedResolutionSelector.visible || !Cura.MachineManager.isActiveQualitySupported
        }

        Item { height: UM.Theme.getSize("default_margin").height } // Spacer

        ProfileWarningReset
        {
            width: parent.width
            visible: (Cura.MachineManager.activeMachine.definition.name != "Omega I60" || profile && profile["advanced_user"]) ? true : false
        }

        Item { height: UM.Theme.getSize("thin_margin").height  + UM.Theme.getSize("narrow_margin").height} // Spacer

        //Line between the sections.
        Rectangle
        {
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        Item { height: UM.Theme.getSize("narrow_margin").height } //Spacer

        Column
        {
            id: settingColumn
            width: parent.width
            spacing: UM.Theme.getSize("thin_margin").height

            Item
            {
                id: recommendedPrintSettingsHeader
                height: childrenRect.height
                width: parent.width
                UM.Label
                {
                    anchors.left: parent.left
                    text: catalog.i18nc("@label", "Recommended print settings")
                    font: UM.Theme.getFont("medium")
                }

                Cura.SecondaryButton
                {
                    id: customSettingsButton
                    anchors.right: parent.right
                    text: catalog.i18nc("@button", "Show Custom")
                    visible : profile && profile["advanced_user"] ? true : false
                    textFont: UM.Theme.getFont("medium_bold")
                    onClicked: onModeChanged()
                }
            }

            RecommendedOmegaSliderSelector
            {
                width: parent.width
                visible : profile && profile["advanced_user"] ? false : true
                selectorText : "Properties"
                quality_key : "omega_properties"
                backgroundTextLeftText : "LIGHTER"
                backgroundTextRightText : "STRONGER"
                sourceIcon : "category_support"
            }

            RecommendedStrengthSelector
            {
                width: parent.width
                visible : profile && profile["advanced_user"] ? true : false
            }

            RecommendedSupportSelector
            {
                width: parent.width
            }

            RecommendedAdhesionSelector
            {
                width: parent.width
            }

            RecommendedFlexibleBuildPlateSelector
            {
                width: parent.width
                visible: Cura.MachineManager.hasFlexibleBed  && (Cura.MachineManager.activeMachine.definition.name == "Epsilon W50" || Cura.MachineManager.activeMachine.definition.name == "Epsilon W27" || Cura.MachineManager.activeMachine.definition.name == "Sigma D25")
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: extrudersEnabledCount
        containerStack: Cura.MachineManager.activeMachine
        key: "extruders_enabled_count"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }
}

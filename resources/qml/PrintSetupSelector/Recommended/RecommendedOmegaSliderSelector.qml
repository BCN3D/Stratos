// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.7 as Cura

Item {
    height: childrenRect.height

    property int leftColumnWidth: Math.floor(width * 0.35)
    property string selectorText : ""
    property string quality_key: ""
    property string backgroundTextLeftText: ""
    property string backgroundTextRightText: ""
    property string tooltipText: catalog.i18nc("@action:label", "Print settings:<br/>Wall line count: %1<br/> Top layers: %2<br/> Bottom layers : %3<br/> Infill Spare Density: %4%").arg(wallLineCountValue).arg(topLayersValue).arg(bottomLayersValue).arg(infillSpareDensityValue)
    property string sourceIcon: ""
    property string infoCharacter : ""
    property string colorText : UM.Theme.getColor("text")
    property int lengthProperty : 3
    property string topLayersValue : topLayers.properties.value
    property string bottomLayersValue : bottomLayers.properties.value
    property string wallLineCountValue : wallLineCount.properties.value
    property string infillSpareDensityValue : infillSpareDensity.properties.value




    // We use a binding to make sure that after manually setting omegaQualitySlider.value it is still bound to the property provider
   Binding
    {
        target: omegaQualitySlider
        property: "value"
        value: {
            return parseInt(omegaQuality.properties.value)
        }
    }

    Binding
    {
        target: qualityRowTitle
        property: "text"
        value: {
            return catalog.i18nc("@label", selectorText) + infoCharacter
        }
    }

    Cura.IconWithText
    {
        id: qualityRowTitle
        text: catalog.i18nc("@label", selectorText) + infoCharacter
        width: leftColumnWidth
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        source: UM.Theme.getIcon(sourceIcon)
        spacing: UM.Theme.getSize("default_margin").width
        iconSize: UM.Theme.getSize("medium_button_icon").width
        color : colorText
        iconColor: colorText
        font: UM.Theme.getFont("medium_bold")
    }

    MouseArea
    {
        id: tooltipArea
        anchors.fill: qualityRowTitle
        propagateComposedEvents: true
        hoverEnabled: true
        onEntered: {
            updateQualities()
            colorText = UM.Theme.getColor("text")
            infoCharacter = ""
            updateQualities()
            base.showTooltip(parent, Qt.point(-UM.Theme.getSize("thick_margin").width, 0), tooltipText)
        }
        onExited: base.hideTooltip()
    }

    Item
    {
        id: omegaQualitySliderContainer
        height: childrenRect.height

        anchors
        {
            left: qualityRowTitle.right
            right: omegaQualitySlider.right
            verticalCenter: qualityRowTitle.verticalCenter
        }

        Text
        {
            id: backgroundTextLeft
            text: backgroundTextLeftText
            font.pixelSize: 8
            color: UM.Theme.getColor("text")
            anchors{
                right: omegaQualitySlider.left + 10
                verticalCenter: qualityRowTitle.verticalCenter

            }
        }

        Text
        {
            id: backgroundTextRight
            text: backgroundTextRightText
            color: UM.Theme.getColor("text")
            font.pixelSize: 8
            anchors{
                right: omegaQualitySlider.right
                verticalCenter: qualityRowTitle.verticalCenter

            }
        }


        CustomSlider {
            id: omegaQualitySlider
            from: 1
            to: lengthProperty
            stepSize: 1

            // set initial value from stack
            value: parseInt(omegaQuality.properties.value)

            onValueChanged:
            {
                if (!omegaQuality.properties.value || parseInt(omegaQuality.properties.value) == omegaQualitySlider.value)
                {
                    return
                }        

                // Otherwise if I change the value in the Custom mode the Recomended view will try to repeat
                // same operation
                var active_mode = UM.Preferences.getValue("cura/active_mode")

                if (active_mode == 0 || active_mode == "simple")
                {
                    updateQualities()
                    infoCharacter = " ⓘ"
                    colorText = UM.Theme.getColor("secondary_button")

                    Cura.MachineManager.setSettingForAllExtruders( quality_key, "value", parseInt(omegaQualitySlider.value))
                }
            }
        }
    }

    function updateQualities(){
        topLayers.forcePropertiesChanged()
        topLayersValue = topLayers.properties.value
        bottomLayers.forcePropertiesChanged()
        bottomLayersValue = bottomLayers.properties.value
        wallLineCount.forcePropertiesChanged()
        wallLineCountValue = wallLineCount.properties.value
        var infillValue = parseInt(originalInfillSpareDensity.properties.value) * parseInt(omegaQualitySlider.value)
        Cura.MachineManager.setSettingForAllExtruders( "infill_sparse_density", "value", parseInt(infillValue))
        infillSpareDensity.forcePropertiesChanged()
    }

    
    property var wallLineCount : UM.SettingPropertyProvider
    {
        id: wallLineCount
        containerStack: Cura.MachineManager.activeStack
        key: "wall_line_count"
        watchedProperties: [ "value" ]
    }

    property var topLayers : UM.SettingPropertyProvider
    {
        id: topLayers
        containerStack: Cura.MachineManager.activeStack
        key: "top_layers"
        watchedProperties: [ "value" ]
    }

    property var bottomLayers : UM.SettingPropertyProvider
    {
        id: bottomLayers
        containerStack: Cura.MachineManager.activeStack
        key: "bottom_layers"
        watchedProperties: [ "value" ]
    }

    property var infillSpareDensity : UM.SettingPropertyProvider
    {
        id: infillSpareDensity
        containerStack: Cura.MachineManager.activeStack
        key: "infill_sparse_density"
        watchedProperties: [ "value" ]
    }

    property var originalInfillSpareDensity : UM.SettingPropertyProvider
    {
        id: originalInfillSpareDensity
        containerStack: Cura.MachineManager.activeStack
        key: "original_infill_sparse_density"
        watchedProperties: [ "value" ]
    }


    property var omegaQuality : UM.SettingPropertyProvider
    {
        id: omegaQuality
        containerStack: Cura.MachineManager.activeStack
        key: quality_key
        watchedProperties: [ "value" ]
    }

}

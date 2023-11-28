// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura

Button
{
    id: objectItemButton

    width: parent.width
    height: UM.Theme.getSize("action_button").height
    checkable: true
    hoverEnabled: true

    onHoveredChanged:
    {
        if(hovered && (buttonTextMetrics.elidedText != buttonText.text || perObjectSettingsInfo.visible))
        {
            tooltip.show()
        } else
        {
            tooltip.hide()
        }
    }


    onClicked: Cura.SceneController.changeSelection(index)

    background: Rectangle
    {
        id: backgroundRect
        color: objectItemButton.hovered ? UM.Theme.getColor("action_button_hovered") : "transparent"
        radius: UM.Theme.getSize("action_button_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: objectItemButton.checked ? UM.Theme.getColor("primary") : "transparent"
    }

    contentItem: Item
    {
        width: objectItemButton.width - objectItemButton.leftPadding
        height: UM.Theme.getSize("action_button").height

        Rectangle
        {
            id: swatch
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            width: UM.Theme.getSize("standard_arrow").height
            height: UM.Theme.getSize("standard_arrow").height
            radius: Math.round(width / 2)
            color: extruderColor
            visible: showExtruderSwatches && extruderColor != ""
        }

        UM.Label
        {
            id: buttonText
            anchors
            {
                left: showExtruderSwatches ? swatch.right : parent.left
                leftMargin: showExtruderSwatches ? UM.Theme.getSize("narrow_margin").width : 0
                right: perObjectSettingsInfo.visible ? perObjectSettingsInfo.left : parent.right
                verticalCenter: parent.verticalCenter
            }
            text: objectItemButton.text
            color: UM.Theme.getColor("text_scene")
            opacity: (outsideBuildArea) ? 0.5 : 1.0
            visible: text != ""
            elide: Text.ElideRight
        }

        Button
        {
            id: perObjectSettingsInfo

            anchors
            {
                right: parent.right
                rightMargin: 0
            }
            width: meshTypeIcon.width + perObjectSettingsCountLabel.width + UM.Theme.getSize("narrow_margin").width
            height: parent.height
            padding: 0
            leftPadding: UM.Theme.getSize("thin_margin").width
            visible: meshType != "" || perObjectSettingsCount > 0

            onClicked:
            {
                Cura.SceneController.changeSelection(index)
                UM.Controller.setActiveTool("PerObjectSettingsTool")
            }

            property string tooltipText:
            {
                var result = "";
                if (!visible)
                {
                    return result;
                }
                if (meshType != "")
                {
                    result += "<br>";
                    switch (meshType) {
                        case "support_mesh":
                            result += catalog.i18nc("@label", "Is printed as support.");
                            break;
                        case "cutting_mesh":
                            result += catalog.i18nc("@label", "Other models overlapping with this model are modified.");
                            break;
                        case "infill_mesh":
                            result += catalog.i18nc("@label", "Infill overlapping with this model is modified.");
                            break;
                        case "anti_overhang_mesh":
                            result += catalog.i18nc("@label", "Overlaps with this model are not supported.");
                            break;
                    }
                }
                if (perObjectSettingsCount != "")
                {
                    result += "<br>" + catalog.i18ncp(
                        "@label %1 is the number of settings it overrides.", "Overrides %1 setting.", "Overrides %1 settings.", perObjectSettingsCount
                    ).arg(perObjectSettingsCount);
                }
                return result;
            }

            contentItem: Item
            {
                height: parent.height
                width: perObjectSettingsInfo.width

                Cura.NotificationIcon
                {
                    id: perObjectSettingsCountLabel
                    anchors
                    {
                        right: parent.right
                        rightMargin: 0
                    }
                    visible: perObjectSettingsCount > 0
                    color: UM.Theme.getColor("text_scene")
                    labelText: perObjectSettingsCount.toString()
                }

                UM.ColorImage
                {
                    id: meshTypeIcon
                    anchors
                    {
                        right: perObjectSettingsCountLabel.left
                        rightMargin: UM.Theme.getSize("narrow_margin").width
                    }

                    width: parent.height
                    height: parent.height
                    color: UM.Theme.getColor("text_scene")
                    visible: meshType != ""
                    source:
                    {
                        switch (meshType) {
                            case "support_mesh":
                                return UM.Theme.getIcon("MeshTypeSupport");
                            case "cutting_mesh":
                            case "infill_mesh":
                                return UM.Theme.getIcon("MeshTypeIntersect");
                            case "anti_overhang_mesh":
                                return UM.Theme.getIcon("BlockSupportOverlaps");
                        }
                        return "";
                    }
                }
            }

            background: Item {}
        }
    }

    TextMetrics
    {
        id: buttonTextMetrics
        text: buttonText.text
        font: buttonText.font
        elide: buttonText.elide
        elideWidth: buttonText.width
    }

    UM.ToolTip
    {
        id: tooltip
        tooltipText: objectItemButton.text + perObjectSettingsInfo.tooltipText
    }

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }
}

// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM
import Cura 1.0 as Cura

Item
{

    // An Item whose bounds are guaranteed to be safe for overlays to be placed.
    // Defaults to parent, ie. the entire available area
    property var safeArea: parent

    // Subtract the actionPanel from the safe area. This way the view won't draw interface elements under/over it
    Item
    {
        id: childSafeArea
        x: safeArea.x - parent.x
        y: safeArea.y - parent.y
        width: actionPanelWidget.x - x
        height: actionPanelWidget.y - y
    }

    Loader
    {
        id: previewMain
        anchors.fill: parent

        source: UM.Controller.activeView != null && UM.Controller.activeView.mainComponent != null ? UM.Controller.activeView.mainComponent : ""

        onLoaded:
        {
            if (previewMain.item.safeArea !== undefined){
               previewMain.item.safeArea = Qt.binding(function() { return childSafeArea });
            }
        }
    }

    Cura.ActionPanelWidget
    {
        id: actionPanelWidget
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: UM.Theme.getSize("thick_margin").width
        anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
        hasPreviewButton: false
    }
}
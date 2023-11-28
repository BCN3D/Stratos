// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

// Button used to collapse and de-collapse group, or a category, of settings
// the button contains
//   - the title of the category,
//   - an optional icon and
//   - a chevron button to display the colapsetivity of the settings
// Mainly used for the collapsable categories in the settings pannel

import QtQuick 2.2
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.1

import UM 1.5 as UM

Button
{
    id: base

    height: UM.Theme.getSize("section_header").height

    property var expanded: false
    property bool indented: false
    property alias arrow: categoryArrow
    property alias categoryIcon: icon.source
    property alias labelText: categoryLabel.text
    property alias labelFont: categoryLabel.font
    leftPadding: UM.Theme.getSize("narrow_margin").width
    rightPadding: UM.Theme.getSize("narrow_margin").width
    states:
    [
        State
        {
            name: "disabled"
            when: !base.enabled
            PropertyChanges { target: categoryLabel; color: UM.Theme.getColor("setting_category_disabled_text") }
            PropertyChanges { target: icon; color: UM.Theme.getColor("setting_category_disabled_text") }
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_category_disabled") }
        },
        State
        {
            name: "hovered"
            when: base.hovered
            PropertyChanges { target: categoryLabel; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: icon; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_category_hover") }
        },
        State
        {
            name: "active"
            when: base.pressed || base.activeFocus
            PropertyChanges { target: categoryLabel; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: icon; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_category") }
        }
    ]

    background: Rectangle
    {
        id: backgroundRectangle

        color: UM.Theme.getColor("setting_category")
        Behavior on color { ColorAnimation { duration: 50 } }

        // Lining on top
        Rectangle
        {
            anchors.top: parent.top
            color: UM.Theme.getColor("border_main")
            height: UM.Theme.getSize("default_lining").height
            width: parent.width
        }
    }

    contentItem: Item
    {
        id: content
        //spacing: UM.Theme.getSize("narrow_margin").width

        UM.ColorImage
        {
            id: icon
            source: ""
            visible: icon.source != ""
            anchors.verticalCenter: parent.verticalCenter
            color: UM.Theme.getColor("setting_category_text")
            width: visible ? UM.Theme.getSize("section_icon").width: 0
            height: UM.Theme.getSize("section_icon").height
            anchors.leftMargin: base.indented ? UM.Theme.getSize("default_margin").width: 0
        }

        UM.Label
        {
            id: categoryLabel
            Layout.fillWidth: true
            anchors.right: categoryArrow.left
            anchors.left: icon.right
            anchors.leftMargin: base.indented ? UM.Theme.getSize("default_margin").width + UM.Theme.getSize("narrow_margin").width: UM.Theme.getSize("narrow_margin").width
            anchors.verticalCenter: parent.verticalCenter
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
            font: UM.Theme.getFont("medium_bold")
            color: UM.Theme.getColor("setting_category_text")
        }

        UM.ColorImage
        {
            id: categoryArrow
            anchors.right: parent.right
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            anchors.verticalCenter: parent.verticalCenter
            color: UM.Theme.getColor("setting_control_button")
            source: expanded ? UM.Theme.getIcon("ChevronSingleDown") : UM.Theme.getIcon("ChevronSingleLeft")
        }
    }
}
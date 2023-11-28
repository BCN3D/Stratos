// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura

// The expandable component has 2 major sub components:
//      * The headerItem; Always visible and should hold some info about what happens if the component is expanded
//      * The contentItem; The content that needs to be shown if the component is expanded.
Item
{
    id: base

    // Enumeration with the different possible alignments of the content with respect of the headerItem
    enum ContentAlignment
    {
        AlignLeft,
        AlignRight
    }

    // The headerItem holds the QML item that is always displayed.
    property alias headerItem: headerItemLoader.sourceComponent

    // The contentItem holds the QML item that is shown when the "open" button is pressed
    property alias contentItem: content.contentItem

    // If the contentItem is a Layout (eg Column) you must use these to set the popup size otherwise you end up with a
    // binding loop between the popup and the contentItem
    // ImplicitWidth/ImplicitHeight can be used instead in the contentItem if it is not a Layout.
    property alias contentWidth: content.width
    property alias contentHeight: content.height

    property color contentBackgroundColor: UM.Theme.getColor("action_button")

    property color headerBackgroundColor: UM.Theme.getColor("action_button")
    property color headerActiveColor: UM.Theme.getColor("expandable_active")
    property color headerHoverColor: UM.Theme.getColor("expandable_hover")

    property alias mouseArea: headerMouseArea
    property alias enabled: headerMouseArea.enabled

    // Text to show when this component is disabled
    property alias disabledText: disabledLabel.text

    // Defines the alignment of the content with respect of the headerItem, by default to the right
    property int contentAlignment: ExpandablePopup.ContentAlignment.AlignRight

    // How much spacing is needed around the contentItem
    property alias contentPadding: content.padding

    // How much padding is needed around the header & button
    property alias headerPadding: background.padding

    property alias headerBackgroundBorder: background.border

    // Whether or not to show the background border
    property bool enableHeaderBackgroundBorder: true

    // What icon should be displayed on the right.
    property alias iconSource: collapseButton.source

    property alias iconColor: collapseButton.color

    // The icon size (it's always drawn as a square)
    property alias iconSize: collapseButton.height

    // Is the "drawer" open?
    readonly property alias expanded: content.visible

    property alias expandedHighlightColor: expandedHighlight.color

    // What should the radius of the header be. This is also influenced by the headerCornerSide
    property alias headerRadius: background.radius

    // On what side should the header corners be shown? 1 is down, 2 is left, 3 is up and 4 is right.
    property alias headerCornerSide: background.cornerSide

    // Change the contentItem close behaviour
    property alias contentClosePolicy : content.closePolicy

    // Distance between the header and the content.
    property int popupOffset: 2 * UM.Theme.getSize("default_lining").height

    onEnabledChanged:
    {
        if (!base.enabled && expanded)
        {
            toggleContent()
        }
    }

    function toggleContent()
    {
        if (content.visible)
        {
            content.close()
        }
        else
        {
            content.open()
        }
    }

    // Add this binding since the background color is not updated otherwise
    Binding
    {
        target: background
        property: "color"
        value: base.enabled ? headerBackgroundColor : UM.Theme.getColor("disabled")
    }

    implicitHeight: 100 * screenScaleFactor
    implicitWidth: 400 * screenScaleFactor

    RoundedRectangle
    {
        id: background
        property real padding: UM.Theme.getSize("default_margin").width

        border.width: base.enableHeaderBackgroundBorder ? UM.Theme.getSize("default_lining").width : 0
        border.color: UM.Theme.getColor("lining")

        color: base.enabled ? headerBackgroundColor : UM.Theme.getColor("disabled")
        anchors.fill: parent

        UM.Label
        {
            id: disabledLabel
            visible: !base.enabled
            leftPadding: background.padding
            text: ""
            height: parent.height
        }

        Item
        {
            anchors.fill: parent
            visible: base.enabled

            MouseArea
            {
                id: headerMouseArea
                anchors.fill: parent
                onClicked: toggleContent()
                hoverEnabled: true
                onEntered: background.color = headerHoverColor
                onExited: background.color = base.enabled ? headerBackgroundColor : UM.Theme.getColor("disabled")
            }

            Loader
            {
                id: headerItemLoader
                anchors
                {
                    left: parent.left
                    right: collapseButton.visible ? collapseButton.left : parent.right
                    top: parent.top
                    bottom: parent.bottom
                    margins: background.padding
                }
            }

            // A highlight that is shown when the content is expanded
            Rectangle
            {
                id: expandedHighlight
                width: parent.width
                height: UM.Theme.getSize("thick_lining").height
                color: UM.Theme.getColor("primary")
                visible: expanded
                anchors.bottom: parent.bottom
            }

            UM.ColorImage
            {
                id: collapseButton
                anchors
                {
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    margins: background.padding
                }
                source: UM.Theme.getIcon("ChevronSingleDown")
                visible: source != ""
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height
                color: UM.Theme.getColor("small_button_text")
            }
        }

    }

    Popup
    {
        id: content

        // Ensure that the content is located directly below the headerItem
        y: background.height + base.popupOffset

        // Make the content aligned with the rest, using the property contentAlignment to decide whether is right or left.
        // In case of right alignment, the 3x padding is due to left, right and padding between the button & text.
        x: contentAlignment == ExpandablePopup.ContentAlignment.AlignRight ? -width + collapseButton.width + headerItemLoader.width + 3 * background.padding : 0
        padding: UM.Theme.getSize("default_margin").width
        closePolicy: Popup.CloseOnPressOutsideParent

        background: Cura.RoundedRectangle
        {
            cornerSide: Cura.RoundedRectangle.Direction.Down
            color: contentBackgroundColor
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")
            radius: UM.Theme.getSize("default_radius").width
            height: contentItem.implicitHeight || content.height
        }

        contentItem: Item {}
    }
}

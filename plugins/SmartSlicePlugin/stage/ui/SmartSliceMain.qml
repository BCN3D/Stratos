//  API Imports
import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.1
import QtGraphicalEffects 1.0

import UM 1.3 as UM
import Cura 1.0 as Cura

import SmartSlice 1.0 as SmartSlice

//  Main UI Stage Components
Item {
    id: smartSliceMain

    property var proxy: UM.Controller.activeStage.proxy
    property var api: UM.Controller.activeStage.api
    property var urlHandler: SmartSlice.URLHandler{}

    //  Main Stage Accessible Properties
    property int smartLoads : 0
    property int smartAnchors : 0

    SmartSlice.SmartSliceMessage {
        anchors {
            horizontalCenter: parent.horizontalCenter
            top: parent.verticalCenter
            topMargin: -(childrenRect.height / 2) + UM.Theme.getSize("default_margin").height
            bottom: parent.bottom
            bottomMargin:  UM.Theme.getSize("default_margin").height * 8
        }
        width: childrenRect.width
    }


    //  1.) Brand Logo
    Image {
        id: tetonBranding
        anchors {
            left: parent.left
            top: parent.top
            leftMargin: UM.Theme.getSize("thick_margin").width
            topMargin: 3 * UM.Theme.getSize("thick_margin").height
        }
        z: 1

        width: 0.125 * smartSliceMain.width
        fillMode: Image.PreserveAspectFit
        source: "../images/smartslice_logo.png"
        opacity: 0.5
        mipmap: true

        visible: !loginDialog.visible
    }

    //  2.) SmartSlice window which holds all of the controls for validate / optimize, and results viewing
    //      This is basically the same thing as ActionPanelWidget in Cura
    Rectangle {
        id: smartSliceWindow //    TODO: Change to Widget when everything works

        width: UM.Theme.getSize("action_panel_widget").width
        height: mainColumn.height + 2 * UM.Theme.getSize("thick_margin").height

        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: UM.Theme.getSize("thick_margin").width
        anchors.bottomMargin: UM.Theme.getSize("thick_margin").height

        color: UM.Theme.getColor("main_background")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")
        radius: UM.Theme.getSize("default_radius").width

        // A single column to hold all of our objects
        Column {
            id: mainColumn

            width: parent.width
            spacing: UM.Theme.getSize("thin_margin").height

            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
                rightMargin: UM.Theme.getSize("thick_margin").width
                leftMargin: UM.Theme.getSize("thick_margin").width
                bottomMargin: UM.Theme.getSize("thick_margin").height
                topMargin: UM.Theme.getSize("thick_margin").height
            }

            // The first row of the column, which holds the status messages and info icons
            RowLayout {
                width: parent.width

                // First column of the row holding the status messages
                Column {
                    id: statusColumn

                    Layout.fillWidth: true

                    spacing: UM.Theme.getSize("thin_margin").height

                    // Main status message
                    Label {
                        id: mainMessage
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        font: smartSliceMain.proxy.isValidated ? UM.Theme.getFont("medium_bold") : UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        renderType: Text.NativeRendering

                        text: smartSliceMain.proxy.sliceStatus
                        visible: smartSliceMain.proxy.sliceStatus != ""
                    }

                    UM.ProgressBar {
                        id: jobProgressBar
                        width: mainColumn.width
                        height: UM.Theme.getSize("progressbar").height

                        Binding {
                            target: jobProgressBar
                            property: "value"
                            value: smartSliceMain.proxy.jobProgress / 100.0
                        }

                        visible: smartSliceMain.proxy.progressBarVisible
                    }

                    // Secondary status message with hint
                    Label {
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        renderType: Text.NativeRendering

                        text: smartSliceMain.proxy.sliceHint
                        visible: smartSliceMain.proxy.sliceHint != ""
                    }

                    // Optimized message
                    Cura.IconWithText {
                        id: estimatedTime
                        width: parent.width

                        text: smartSliceMain.proxy.resultTimeTotal.getDisplayString(UM.DurationFormat.Long)

                        source: UM.Theme.getIcon("clock")
                        font: UM.Theme.getFont("medium_bold")

                        visible: smartSliceMain.proxy.isOptimized
                    }

                    Cura.IconWithText {
                        id: estimatedCosts
                        width: parent.width

                        text: {
                            var totalLengths = 0
                            var totalWeights = 0
                            var totalCosts = 0.0
                            if (smartSliceMain.proxy.materialLength > 0) {
                                totalLengths = smartSliceMain.proxy.materialLength
                                totalWeights = smartSliceMain.proxy.materialWeight.toFixed(2)
                                totalCosts = smartSliceMain.proxy.materialCost.toFixed(2)
                            }
                            if(totalCosts > 0)
                            {
                                var costString = "%1 %2".arg(UM.Preferences.getValue("cura/currency")).arg(totalCosts)
                                return totalWeights + "g · " + totalLengths.toFixed(2) + "m · " + costString
                            }
                            return totalWeights + "g · " + totalLengths.toFixed(2) + "m"
                        }
                        source: UM.Theme.getIcon("spool")
                        font: UM.Theme.getFont("default")

                        visible: smartSliceMain.proxy.isOptimized
                    }
                }

                // Second column in the top row, holding the status indicator
                Column {
                    id: smartSliceInfoColumn

                    Layout.alignment: Qt.AlignTop

                    // Status indicator (info image) which has the popup
                    Image {
                        id: smartSliceInfoIcon

                        width: UM.Theme.getSize("section_icon").width
                        height: UM.Theme.getSize("section_icon").height

                        anchors.right: parent.right

                        fillMode: Image.PreserveAspectFit
                        mipmap: true

                        source: smartSliceMain.proxy.sliceIconImage
                        visible: smartSliceMain.proxy.sliceIconVisible

                        Connections {
                            target: smartSliceMain.proxy
                            onSliceIconImageChanged: {
                                smartSliceInfoIcon.source = smartSliceMain.proxy.sliceIconImage
                            }
                            onSliceIconVisibleChanged: {
                                smartSliceInfoIcon.visible = smartSliceMain.proxy.sliceIconVisible
                                smartSliceInfoColumn.forceLayout()
                                statusColumn.forceLayout()
                                mainColumn.forceLayout()
                            }
                            onSliceInfoOpenChanged: {
                                if (smartSliceMain.proxy.sliceInfoOpen) {
                                    smartSlicePopup.open()
                                }
                            }
                        }

                        MouseArea
                        {
                            anchors.fill: parent
                            hoverEnabled: true
                            onEntered: {
                                if (visible) {
                                    smartSlicePopup.open();
                                }
                            }
                            onExited: smartSlicePopup.close()
                        }

                        // Popup message with slice results
                        Popup {
                            id: smartSlicePopup

                            y: -(height + UM.Theme.getSize("default_arrow").height + UM.Theme.getSize("thin_margin").height)
                            x: parent.width - width + UM.Theme.getSize("thin_margin").width

                            contentWidth: UM.Theme.getSize("action_panel_information_widget").width
                            contentHeight: smartSlicePopupContents.height

                            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

                            opacity: opened ? 1 : 0
                            Behavior on opacity { NumberAnimation { duration: 100 } }

                            Column {
                                id: smartSlicePopupContents

                                width: parent.width

                                spacing: UM.Theme.getSize("default_margin").width

                                property var header_font: UM.Theme.getFont("default_bold")
                                property var header_color: UM.Theme.getColor("primary")
                                property var subheader_font: UM.Theme.getFont("default")
                                property var subheader_color: "#A9A9A9"
                                property var description_font: UM.Theme.getFont("default")
                                property var description_color: UM.Theme.getColor("text")
                                property var value_font: UM.Theme.getFont("default")
                                property var value_color: UM.Theme.getColor("text")

                                property color warningColor: "#F3BA1A"
                                property color errorColor: "#F15F63"
                                property color successColor: "#5DBA47"

                                property var col1_width: 0.45
                                property var col2_width: 0.3
                                property var col3_width: 0.25

                                Column {
                                    id: requirements

                                    width: parent.width
                                    topPadding: UM.Theme.getSize("default_margin").height
                                    leftPadding: UM.Theme.getSize("default_margin").width
                                    rightPadding: UM.Theme.getSize("default_margin").width

                                    /* REQUIREMENTS HEADER */
                                    Label {
                                        font: smartSlicePopupContents.header_font
                                        color: smartSlicePopupContents.header_color
                                        renderType: Text.NativeRendering

                                        text: "REQUIREMENTS"
                                    }

                                    Row {
                                        id: layoutRequirements
                                        width: parent.width

                                        Column {
                                            width: smartSlicePopupContents.col1_width * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                width: parent.width
                                                bottomPadding: UM.Theme.getSize("thin_margin").height

                                                font: smartSlicePopupContents.subheader_font
                                                color: smartSlicePopupContents.subheader_color

                                                text: "Objective"
                                            }
                                            Label {
                                                id: labelDescriptionSafetyFactor

                                                width: parent.width

                                                font: smartSlicePopupContents.description_font
                                                color: smartSliceMain.proxy.safetyFactorColor
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: "Factor of Safety:"
                                            }
                                            Label {
                                                id: labelDescriptionMaximumDisplacement

                                                width: parent.width

                                                font: smartSlicePopupContents.description_font
                                                color: smartSliceMain.proxy.maxDisplaceColor
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: "Max Displacement:"
                                            }
                                        }
                                        Column {
                                            id: secondColumnPopup
                                            width: smartSlicePopupContents.col2_width * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                width: parent.width
                                                bottomPadding: UM.Theme.getSize("thin_margin").height

                                                horizontalAlignment: Text.AlignHCenter
                                                font: smartSlicePopupContents.subheader_font
                                                color: smartSlicePopupContents.subheader_color

                                                text: "Computed"
                                            }
                                            Label {
                                                id: labelResultSafetyFactor
                                                width: parent.width

                                                horizontalAlignment: Text.AlignHCenter
                                                font: smartSlicePopupContents.value_font
                                                color: smartSliceMain.proxy.safetyFactorColor
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                Connections {
                                                    target: smartSliceMain.proxy
                                                    onResultSafetyFactorChanged: {
                                                        labelResultSafetyFactor.text = parseFloat(Math.round(smartSliceMain.proxy.resultSafetyFactor * 1000) / 1000).toFixed(2)
                                                    }
                                                }

                                                text: parseFloat(Math.round(smartSliceMain.proxy.resultSafetyFactor * 1000) / 1000).toFixed(2)
                                            }
                                            Label {
                                                id: labelResultMaximalDisplacement

                                                width: parent.width

                                                horizontalAlignment: Text.AlignHCenter
                                                font: smartSlicePopupContents.value_font
                                                color: smartSliceMain.proxy.maxDisplaceColor
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                Connections {
                                                    target: smartSliceMain.proxy
                                                    onResultMaximalDisplacementChanged: {
                                                        labelResultMaximalDisplacement.text = parseFloat(Math.round(smartSliceMain.proxy.resultMaximalDisplacement * 1000) / 1000).toFixed(2)
                                                    }
                                                }

                                                text: parseFloat(Math.round(smartSliceMain.proxy.resultMaximalDisplacement * 1000) / 1000).toFixed(2)
                                            }
                                        }
                                        Column {
                                            id: thirdColumnPopup
                                            width: smartSlicePopupContents.col3_width * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                width: parent.width
                                                bottomPadding: UM.Theme.getSize("thin_margin").height

                                                horizontalAlignment: Text.AlignRight
                                                font: smartSlicePopupContents.subheader_font
                                                color: smartSlicePopupContents.subheader_color

                                                text: "Target"
                                            }
                                            Label {
                                                id: labelTargetSafetyFactor

                                                width: parent.width

                                                horizontalAlignment: Text.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSliceMain.proxy.safetyFactorColor
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                Connections {
                                                    target: smartSliceMain.proxy
                                                    onTargetSafetyFactorChanged: {
                                                        labelTargetSafetyFactor.text = parseFloat(Math.round(smartSliceMain.proxy.targetSafetyFactor * 1000) / 1000).toFixed(2)
                                                    }
                                                }

                                                text: parseFloat(Math.round(smartSliceMain.proxy.targetSafetyFactor * 1000) / 1000).toFixed(2)
                                            }
                                            Label {
                                                id: labelTargetMaximalDisplacement

                                                width: parent.width

                                                horizontalAlignment: Text.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSliceMain.proxy.maxDisplaceColor
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                Connections {
                                                    target: smartSliceMain.proxy
                                                    onTargetMaximalDisplacementChanged: {
                                                        labelTargetMaximalDisplacement.text = parseFloat(Math.round(smartSliceMain.proxy.targetMaximalDisplacement * 1000) / 1000).toFixed(2)
                                                    }
                                                }

                                                text: parseFloat(Math.round(smartSliceMain.proxy.targetMaximalDisplacement * 1000) / 1000).toFixed(2)
                                            }
                                        }
                                    }
                                }


                                /* TIME ESTIMATION HEADER */
                                Column {
                                    id: timeEstimation

                                    width: parent.width
                                    leftPadding: UM.Theme.getSize("default_margin").width
                                    rightPadding: UM.Theme.getSize("default_margin").width

                                    Label {
                                        font: smartSlicePopupContents.header_font
                                        color: smartSlicePopupContents.header_color

                                        text: "TIME ESTIMATION"
                                    }

                                    Row {
                                        width: parent.width

                                        Column {
                                            width: smartSlicePopupContents.col1_width * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                text: "Print time:"

                                                width: parent.width

                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText
                                            }
                                            /*
                                            Label {
                                                Layout.fillWidth: true

                                                text: "Infill:"

                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color
                                            }
                                            Label {
                                                text: "Inner Walls:"

                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color
                                            }
                                            Label {
                                                text: "Outer Walls:"

                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color
                                            }
                                            Label {
                                                text: "Retractions:"

                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color
                                            }
                                            Label {
                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color

                                                text: "Skin:"
                                            }
                                            Label {
                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color

                                                text: "Skirt:"
                                            }
                                            Label {
                                                font: smartSlicePopupContents.description_font
                                                color: smartSlicePopupContents.description_color

                                                text: "Travel:"
                                            }
                                            */
                                        }

                                        Column {
                                            width: smartSlicePopupContents.col2_width * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {

                                                width: parent.width

                                                horizontalAlignment: Text.AlignHCenter
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: smartSliceMain.proxy.resultTimeTotal.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)
                                            }
                                            /*
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.resultTimeInfill.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.resultTimeInnerWalls.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.resultTimeOuterWalls.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.resultTimeRetractions.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.resultTimeSkin.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.resultTimeSkirt.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color.getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)

                                                smartSliceMain.proxy.resultTimeTravel
                                            }
                                            */
                                        }

                                        Column {
                                            width: smartSlicePopupContents.col3_width * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {

                                                width: parent.width

                                                horizontalAlignment: Text.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: "100 %"
                                            }
                                            /*
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.percentageTimeInfill.toFixed(2) + " %"
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.percentageTimeInnerWalls.toFixed(2) + " %"
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.percentageTimeOuterWalls.toFixed(2) + " %"
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.percentageTimeRetractions.toFixed(2) + " %"
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.percentageTimeSkin.toFixed(2) + " %"
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.percentageTimeSkirt.toFixed(2) + " %"
                                            }
                                            Label {
                                                Layout.alignment: Qt.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color

                                                text: smartSliceMain.proxy.percentageTimeTravel.toFixed(2) + " %"
                                            }
                                            */
                                        }
                                    }
                                }

                                Column {
                                    id: materialEstimate
                                    width: parent.width

                                    leftPadding: UM.Theme.getSize("default_margin").width
                                    rightPadding: UM.Theme.getSize("default_margin").width
                                    bottomPadding: UM.Theme.getSize("default_margin").height

                                    /* Material ESTIMATION HEADER */
                                    Label {
                                        font: smartSlicePopupContents.header_font
                                        color: smartSlicePopupContents.header_color

                                        text: "MATERIAL ESTIMATION"
                                    }

                                    Row {
                                        width: parent.width

                                        Column {
                                            width: 0.25 * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                width: parent.width

                                                font: smartSlicePopupContents.value_font
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: smartSliceMain.proxy.materialName
                                            }
                                        }

                                        Column {
                                            width: 0.25 * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                width: parent.width

                                                horizontalAlignment: Text.AlignRight
                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: smartSliceMain.proxy.materialLength + " m"
                                            }
                                        }

                                        Column {
                                            width: 0.25 * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                width: parent.width

                                                horizontalAlignment: Text.AlignRight

                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: smartSliceMain.proxy.materialWeight.toFixed(2) + " g"
                                            }
                                        }

                                        Column {
                                            width: 0.25 * (parent.width - 2 * UM.Theme.getSize("default_margin").width)

                                            Label {
                                                width: parent.width

                                                Layout.alignment: Qt.AlignRight
                                                horizontalAlignment: Text.AlignRight

                                                font: smartSlicePopupContents.value_font
                                                color: smartSlicePopupContents.value_color
                                                renderType: Text.NativeRendering
                                                textFormat: Text.RichText

                                                text: smartSliceMain.proxy.materialCost.toFixed(2) + " €"
                                            }
                                        }
                                    }
                                }
                            }


                            background: UM.PointingRectangle
                            {
                                color: UM.Theme.getColor("tool_panel_background")
                                borderColor: UM.Theme.getColor("lining")
                                borderWidth: UM.Theme.getSize("default_lining").width

                                target: Qt.point(width - (smartSliceInfoIcon.width / 2) - UM.Theme.getSize("thin_margin").width,
                                                height + UM.Theme.getSize("default_arrow").height - UM.Theme.getSize("thin_margin").height)

                                arrowSize: UM.Theme.getSize("default_arrow").width
                            }
                        }
                    }
                }
            }

            // Holds all of the buttons and sets the height
            Item {
                id: buttons

                width: parent.width
                height: smartSliceButton.height

                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: {
                        if (smartSliceMain.proxy.errorsExist && !smartSliceButton.enabled && !smartSliceWarningPopup.opened) {
                            smartSliceWarningPopup.open();
                        }
                    }
                }

                Cura.PrimaryButton {
                    id: smartSliceButton

                    height: UM.Theme.getSize("action_button").height
                    width: smartSliceSecondaryButton.visible ? 2 / 3 * parent.width - 1 / 2 * UM.Theme.getSize("default_margin").width : parent.width
                    fixedWidthMode: true

                    anchors.right: parent.right
                    anchors.bottom: parent.bottom

                    text: smartSliceMain.proxy.sliceButtonText

                    enabled: smartSliceMain.proxy.sliceButtonEnabled
                    visible: smartSliceMain.proxy.sliceButtonVisible

                    /*
                        SmartSlice Button Click Event
                    */
                    onClicked: {
                        //  Show Validation Dialog
                        smartSliceMain.proxy.sliceButtonClicked()
                    }
                }

                Cura.SecondaryButton {
                    id: smartSliceSecondaryButton

                    height: UM.Theme.getSize("action_button").height
                    width: smartSliceButton.visible ? (
                        visible ? 1 / 3 * parent.width - 1 / 2 * UM.Theme.getSize("default_margin").width : UM.Theme.getSize("thick_margin").width
                        ) : parent.width
                    fixedWidthMode: true

                    anchors.left: parent.left
                    anchors.bottom: parent.bottom

                    text: smartSliceMain.proxy.secondaryButtonText

                    visible: smartSliceMain.proxy.secondaryButtonVisible

                    Connections {
                        target: smartSliceMain.proxy
                        onSecondaryButtonVisibleChanged: { smartSliceSecondaryButton.visible = smartSliceMain.proxy.secondaryButtonVisible }
                        onSecondaryButtonFillWidthChanged: { smartSliceSecondaryButton.Layout.fillWidth = smartSliceMain.proxy.secondaryButtonFillWidth }
                    }

                    /*
                        SmartSlice Button Click Event
                    */
                    onClicked: {
                        //  Show Validation Dialog
                        smartSliceMain.proxy.secondaryButtonClicked()
                    }
                }

                Glow {
                    anchors.fill: smartSliceButton
                    radius: 8
                    samples: 17
                    color: smartSlicePopupContents.warningColor
                    source: smartSliceButton
                    visible: smartSliceMain.proxy.errorsExist
                }

                // Popup message with warning / errors
                Popup {
                    id: smartSliceWarningPopup

                    y: -(height + UM.Theme.getSize("default_arrow").height + UM.Theme.getSize("thin_margin").height)
                    x: parent.width - width + UM.Theme.getSize("thin_margin").width

                    contentWidth: parent.width
                    contentHeight: smartSliceWarningContents.height

                    height: contentHeight + 2 * UM.Theme.getSize("default_margin").width

                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent | smartSliceButton.enabled

                    opacity: opened ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 100 } }

                    Connections {
                        target: smartSliceMain.proxy
                        onSmartSliceErrorsChanged: {
                            smartSliceErrors.forceLayout();
                            smartSliceWarningContents.forceLayout();

                            if (errorRepeater.model.length == 0 && smartSliceWarningPopup.opened) {
                                smartSliceWarningPopup.close();
                                return
                            }
                        }
                    }

                    Column {
                        id: smartSliceWarningContents

                        width: parent.width
                        spacing: UM.Theme.getSize("default_margin").width

                        Column {

                            width: parent.width
                            topPadding: UM.Theme.getSize("default_margin").height
                            leftPadding: UM.Theme.getSize("default_margin").width
                            rightPadding: UM.Theme.getSize("default_margin").width

                            spacing: UM.Theme.getSize("thin_margin").width

                            Label {
                                font: smartSlicePopupContents.header_font
                                color: smartSlicePopupContents.value_color
                                renderType: Text.NativeRendering

                                text: "ITEMS NEED RESOLVED"
                            }

                            Label {
                                font: smartSlicePopupContents.subheader_font
                                color: smartSlicePopupContents.value_color
                                renderType: Text.NativeRendering
                                width: parent.width
                                rightPadding: UM.Theme.getSize("default_margin").width
                                wrapMode: Text.WordWrap
                                text: "The following items need to be resolved before you can validate:"
                            }
                        }

                        ScrollView {
                            property int maxHeight: 14 * UM.Theme.getSize("section_icon").width

                            width: parent.width
                            height: scrollErrors.height > maxHeight ? maxHeight : scrollErrors.height

                            contentWidth: parent.width

                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                            ScrollBar.vertical.policy: ScrollBar.AsNeeded

                            clip: true

                            Item {
                                id: scrollErrors

                                width: parent.width
                                height: smartSliceErrors.height
                                implicitHeight: height

                                Column {
                                    id: smartSliceErrors

                                    function getErrors() {
                                        var errors = smartSliceMain.proxy.errors
                                        var error_text = []
                                        for(var error in errors) {
                                            var error_resolution = []
                                            error_resolution.push(error)
                                            error_resolution.push(errors[error])

                                            error_text.push(error_resolution)
                                        }
                                        return error_text
                                    }

                                    Repeater {
                                        id: errorRepeater
                                        model: smartSliceErrors.getErrors()

                                        Column {
                                            width: parent.width

                                            leftPadding: UM.Theme.getSize("default_margin").width
                                            rightPadding: UM.Theme.getSize("default_margin").width
                                            spacing: UM.Theme.getSize("thin_margin").width

                                            Row {
                                                width: parent.width

                                                UM.RecolorImage {
                                                    id: error_icon

                                                    width: 0.5 * UM.Theme.getSize("section_icon").width
                                                    height: width
                                                    Layout.fillHeight: true
                                                    anchors.verticalCenter: parent.verticalCenter

                                                    source: "../images/circle.png"
                                                    color: smartSlicePopupContents.warningColor
                                                }

                                                Label {
                                                    id: error_label

                                                    width: parent.width - error_icon.width - 3 * UM.Theme.getSize("default_margin").width - UM.Theme.getSize("thin_margin").width
                                                    anchors. verticalCenter: parent.verticalCenter
                                                    leftPadding: UM.Theme.getSize("thin_margin").width
                                                    rightPadding: UM.Theme.getSize("default_margin").width
                                                    Layout.fillHeight: true

                                                    text: modelData[0]
                                                    font: smartSlicePopupContents.value_font
                                                    color: smartSlicePopupContents.value_color
                                                    wrapMode: Text.WordWrap
                                                    verticalAlignment: Text.AlignVCenter
                                                }
                                            }

                                            Row {
                                                width: parent.width
                                                leftPadding: UM.Theme.getSize("thick_margin").width

                                                UM.RecolorImage {
                                                    id: resolution_icon

                                                    width: 0.5 * UM.Theme.getSize("section_icon").width
                                                    height: width
                                                    Layout.fillHeight: true

                                                    anchors.verticalCenter: parent.verticalCenter

                                                    source: "../images/circle.png"
                                                    color: smartSlicePopupContents.successColor
                                                }

                                                Label {
                                                    id: resolution_label

                                                    width: parent.width - resolution_icon.width - 3 * UM.Theme.getSize("default_margin").width - UM.Theme.getSize("thin_margin").width
                                                    anchors. verticalCenter: parent.verticalCenter
                                                    leftPadding: UM.Theme.getSize("thin_margin").width
                                                    rightPadding: UM.Theme.getSize("default_margin").width
                                                    Layout.fillHeight: true

                                                    text: modelData[1]
                                                    font: smartSlicePopupContents.value_font
                                                    color: smartSlicePopupContents.value_color
                                                    wrapMode: Text.WordWrap
                                                    verticalAlignment: Text.AlignVCenter
                                                }
                                            }
                                        }
                                    }

                                    width: parent.width
                                    topPadding: UM.Theme.getSize("default_margin").height
                                    leftPadding: UM.Theme.getSize("default_margin").width
                                    rightPadding: UM.Theme.getSize("default_margin").width
                                    bottomPadding: UM.Theme.getSize("default_margin").width

                                    spacing: UM.Theme.getSize("thin_margin").width
                                }
                            }
                        }
                    }

                    background: UM.PointingRectangle
                    {
                        color: UM.Theme.getColor("tool_panel_background")
                        borderColor: UM.Theme.getColor("lining")
                        borderWidth: UM.Theme.getSize("default_lining").width

                        target: Qt.point(width - (smartSliceSecondaryButton.width / 2) - UM.Theme.getSize("thin_margin").width,
                                        height + UM.Theme.getSize("default_arrow").height - UM.Theme.getSize("thin_margin").height)

                        arrowSize: UM.Theme.getSize("default_arrow").width
                    }
                }
            }
        }
    }

    SmartSlice.SmartSliceResultsButtons {
        id: resultsButtons

        anchors {
            right: smartSliceWindow.left
        }
    }

    SmartSlice.ResultsTable {
        implicitHeight: 0.25 * smartSliceMain.height
        width: 0.4 * smartSliceMain.width

        visible: smartSliceMain.proxy.isOptimized
    }

    SmartSlice.SmartSliceLogin {
        id: loginDialog

        visible: true
    }

    SmartSlice.SmartSliceWelcome {
        id: welcomeDialog

        visible: proxy.introScreenVisible || proxy.welcomeScreenVisible
    }

}

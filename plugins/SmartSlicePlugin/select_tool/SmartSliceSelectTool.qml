import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Controls 2.0 as QTC
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

import SmartSlice 1.0  as SmartSlice

Item {
    id: constraintsTooltip
    width: selectAnchorButton.width * 3 - 3 * UM.Theme.getSize("default_margin").width
    height: {
        if (selectAnchorButton.checked) {
            return selectAnchorButton.height + UM.Theme.getSize("default_margin").width + bcListAnchors.height
        }
        if (selectLoadButton.checked) {
            return selectLoadButton.height + UM.Theme.getSize("default_margin").width + bcListForces.height
        }
    }

    property var model: selectAnchorButton.checked ? bcListAnchors.model : bcListForces.model

    UM.I18nCatalog {
        id: catalog;
        name: "smartslice"
    }

    Component.onCompleted: {
        selectAnchorButton.checked = UM.ActiveTool.properties.getValue("AnchorSelectionActive");
        selectLoadButton.checked = UM.ActiveTool.properties.getValue("LoadSelectionActive");
        faceDialog.comboboxElements();
        faceDialog.update();
    }

    MouseArea {

        propagateComposedEvents: false
        anchors.fill: parent

        Button {
            id: selectAnchorButton
            anchors.left: parent.left
            z: 2

            iconSource: "./media/anchor_icon.svg"
            property bool needBorder: true

            style: UM.Theme.styles.tool_button

            text: catalog.i18nc("@action:button", "<b> Anchors <\b>")

            onClicked: {
                UM.ActiveTool.triggerAction("setAnchorSelection");
                selectAnchorButton.checked = true;
                selectLoadButton.checked = false;
                faceDialog.comboboxElements();
                bcListForces.model.loadMagnitude = loadMagnitudeItem.magnitude;
                faceDialog.update();
            }
        }

        Button {
            id: selectLoadButton

            anchors.left: selectAnchorButton.right;
            anchors.leftMargin: UM.Theme.getSize("default_margin").width;
            z: 1

            iconSource: "./media/load_icon.svg"
            property bool needBorder: true

            style: UM.Theme.styles.tool_button

            text: catalog.i18nc("@action:button", "<b> Loads <\b>")

            onClicked: {
                UM.ActiveTool.triggerAction("setLoadSelection");
                selectAnchorButton.checked = false;
                selectLoadButton.checked = true;
                faceDialog.comboboxElements();
                faceDialog.update();
            }
        }

        SmartSlice.BoundaryConditionList {
            id: bcListAnchors
            visible: selectAnchorButton.checked
            boundaryConditionType: 0

            anchors.left: selectAnchorButton.left
            anchors.top: selectAnchorButton.bottom

            onSelectionChanged: {
                faceDialog.update();
            }

            Connections {
                target: bcListAnchors.model
                onUpdateDialog: {
                    faceDialog.update();
                }
            }
        }

        SmartSlice.BoundaryConditionList {
            id: bcListForces
            visible: selectLoadButton.checked
            boundaryConditionType: 1

            anchors.left: selectAnchorButton.left
            anchors.top: selectAnchorButton.bottom

            onSelectionChanged: {
                faceDialog.update();
                loadMagnitudeItem.magnitude = model.loadMagnitude;
            }

            Connections {
                target: bcListForces.model
                onUpdateDialog: {
                    faceDialog.update();
                }
            }
        }

        Item {
            id: faceDialog

            visible: true

            // width: childrenRect.width
            width: contentRectangle.width + UM.Theme.getSize("default_margin").width + UM.Theme.getSize("tooltip").width
            height: childrenRect.height + UM.Theme.getSize("default_margin").height

            layer.enabled: true

            property var handler: UM.Controller.activeStage.proxy.loadDialog

            property int xStart: constraintsTooltip.x + constraintsTooltip.width + 2 * UM.Theme.getSize("default_margin").width
            property int yStart: constraintsTooltip.y - 1. * UM.Theme.getSize("default_margin").height

            property bool positionSet: handler.positionSet
            property int xPosition: handler.xPosition
            property int yPosition: handler.yPosition

            property var comboModel: comboboxElements()

            property var loadList: ListModel {
                ListElement { key: "Push / Pull"; value: 1 }
            }
            property var anchorList: ListModel {
                ListElement { key: "Fixed"; value: 1 }
            }

            property Component tickmarks: Repeater {
                id: repeater
                model: control.stepSize > 0 ? 1 + (control.maximumValue - control.minimumValue) / control.stepSize : 0
                Rectangle {
                    color: "#777"
                    width: 1 ; height: 3
                    y: repeater.height
                    x: styleData.handleWidth / 2 + index * ((repeater.width - styleData.handleWidth) / (repeater.count-1))
                }
            }

            x: {
                if (handler.positionSet) {
                    return xPosition
                }
                return xStart
            }

            y: {
                if (handler.positionSet) {
                    return yPosition
                }
                return yStart
            }

            z: 3 //-> A hack to get this on the top

            function trySetPosition(posNewX, posNewY) {
                var margin = UM.Theme.getSize("narrow_margin");
                var minPt = base.mapFromItem(null, margin.width, margin.height);
                var maxPt = base.mapFromItem(null,
                    CuraApplication.appWidth() - 1.2 * faceDialog.width,
                    CuraApplication.appHeight() - faceDialog.height - UM.Theme.getSize("action_button").height
                );
                var initialY = minPt.y + 200 * screenScaleFactor;
                var finalY = maxPt.y; //- 200 * screenScaleFactor

                faceDialog.x = Math.max(minPt.x, Math.min(maxPt.x, posNewX));
                faceDialog.y = Math.max(initialY, Math.min(finalY, posNewY));

                faceDialog.handler.setPosition(faceDialog.x, faceDialog.y);
            }

            function comboboxElements() {
                if (selectLoadButton.checked) {
                    comboModel = loadList;
                }
                if (selectAnchorButton.checked) {
                    comboModel = anchorList;
                }
            }

            function update() {
                normalLayout.update();
                customLayout.update();

                normalLayout.visible = constraintsTooltip.model.surfaceSelectionMode == 1;
                customButton.visible = constraintsTooltip.model.surfaceSelectionMode == 1;
                customLayout.visible = constraintsTooltip.model.surfaceSelectionMode == 2;
                normalButton.visible = constraintsTooltip.model.surfaceSelectionMode == 2;

                loadMagnitudeItem.magnitude = bcListForces.model.loadMagnitude;
                loadMagnitudeItem.sliderVisible = selectLoadButton.checked && normalLayout.visible;
                loadHelperImageRect.visible = loadHelperImageRect.isVis();
            }

            Column {
                id: loadColumn

                width: childrenRect.width
                height: childrenRect.height

                spacing: -UM.Theme.getSize("default_lining").width

                MouseArea {
                    cursorShape: Qt.SizeAllCursor

                    height: childrenRect.height
                    width: childrenRect.width

                    property var clickPos: Qt.point(0, 0)
                    property bool dragging: false
                    // property int absoluteMinimumHeight: 200 * screenScaleFactor

                    onPressed: {
                        clickPos = Qt.point(mouse.x, mouse.y);
                        dragging = true
                    }
                    onPositionChanged: {
                        if(dragging) {
                            var delta = Qt.point(mouse.x - clickPos.x, mouse.y - clickPos.y);
                            if (delta.x !== 0 || delta.y !== 0) {
                                faceDialog.trySetPosition(faceDialog.x + delta.x, faceDialog.y + delta.y);
                            }
                        }
                    }
                    onReleased: {
                        dragging = false
                    }
                    onDoubleClicked: {
                        dragging = false
                        faceDialog.trySetPosition(faceDialog.xStart, faceDialog.yStart)
                    }

                    Cura.RoundedRectangle {
                        id: topDragArea
                        width: contentRectangle.width
                        height: UM.Theme.getSize("default_margin").height
                        color: UM.Theme.getColor("secondary")
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")

                        cornerSide: 3
                    }
                }

                Cura.RoundedRectangle {
                    id: contentRectangle

                    color: UM.Theme.getColor("main_background")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    radius: UM.Theme.getSize("default_radius").width

                    height: contentContainer.height + buttonsSeparator.height + buttonRow.height + 3.25 * UM.Theme.getSize("default_margin").width
                    width: contentContainer.width

                    cornerSide: 1

                    MouseArea {
                        id: loadDialogMouseArea
                        propagateComposedEvents: false
                        width: contentRectangle.width
                        height: contentRectangle.height

                        Item {
                            id: contentContainer

                            width: childrenRect.width
                            height: loadMagnitudeItem.visible ? selectionLayout.height + loadMagnitudeItem.height : selectionLayout.height

                            anchors.margins: UM.Theme.getSize("default_margin").width

                            Item {
                                id: selectionLayout

                                anchors.margins: UM.Theme.getSize("default_margin").width

                                width: 2 / 3 * UM.Theme.getSize("action_panel_widget").width + 1.5 * UM.Theme.getSize("default_margin").width
                                height: normalLayout.visible ? normalLayout.height + UM.Theme.getSize("default_margin").width : customLayout.height + UM.Theme.getSize("default_margin").width

                                SmartSlice.NormalLayout {
                                    id: normalLayout

                                    anchors {
                                        top: parent.top
                                        margins: UM.Theme.getSize("default_margin").width
                                    }

                                    width: parent.width

                                    visible: constraintsTooltip.model.surfaceSelectionMode == 1
                                    loadChecked: selectLoadButton.checked

                                    model: constraintsTooltip.model
                                    comboModel: faceDialog.comboModel
                                }

                                SmartSlice.CustomLayout {
                                    id: customLayout

                                    anchors {
                                        left: parent.left
                                        right: parent.right
                                        top: parent.top
                                        margins: UM.Theme.getSize("default_margin").width
                                    }

                                    width: parent.width

                                    visible: constraintsTooltip.model.surfaceSelectionMode == 2
                                    loadChecked: selectLoadButton.checked

                                    model: constraintsTooltip.model
                                    comboModel: faceDialog.comboModel
                                }
                            }

                            SmartSlice.LoadMagnitude {
                                id: loadMagnitudeItem
                                anchors {
                                    left: parent.left
                                    right: parent.right
                                    top: selectionLayout.bottom
                                    margins: UM.Theme.getSize("default_margin").width
                                }
                                visible: selectLoadButton.checked
                                sliderVisible: selectLoadButton.checked && constraintsTooltip.model.surfaceSelectionMode == 1
                                model: bcListForces.model
                            }
                        }

                        Rectangle {
                            id: buttonsSeparator

                            anchors {
                                top: contentContainer.bottom
                                topMargin: UM.Theme.getSize("default_margin").height
                            }
                            width: parent.width
                            height: UM.Theme.getSize("default_lining").height
                            color: UM.Theme.getColor("lining")
                        }

                        Item {
                            id: buttonRow

                            anchors {
                                top: buttonsSeparator.bottom
                                left: parent.left
                                right: parent.right
                            }

                            height: childrenRect.height

                            Cura.SecondaryButton {
                                id: normalButton

                                anchors {
                                    top: parent.top
                                    left: parent.left
                                    margins: UM.Theme.getSize("default_margin").width
                                }

                                leftPadding: UM.Theme.getSize("default_margin").width
                                rightPadding: UM.Theme.getSize("default_margin").width

                                text: catalog.i18nc("@button", "Normal")
                                iconSource: UM.Theme.getIcon("arrow_left")
                                visible: constraintsTooltip.model.surfaceSelectionMode == 2

                                onClicked: {
                                    constraintsTooltip.model.surfaceSelectionMode = 1
                                    constraintsTooltip.model.surfaceType = 1
                                    faceDialog.update()
                                }
                            }

                            Cura.SecondaryButton {
                                id: customButton
                                anchors {
                                    top: parent.top
                                    right: parent.right
                                    margins: UM.Theme.getSize("default_margin").width
                                }

                                leftPadding: UM.Theme.getSize("default_margin").width
                                rightPadding: UM.Theme.getSize("default_margin").width

                                text: catalog.i18nc("@button", "Custom")
                                iconSource: UM.Theme.getIcon("arrow_right")
                                isIconOnRightSide: true
                                visible: constraintsTooltip.model.surfaceSelectionMode == 1
                                onClicked: {
                                    constraintsTooltip.model.surfaceSelectionMode = 2
                                    constraintsTooltip.model.surfaceType = 4
                                    faceDialog.update()
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: loadHelperImageRect

                function isVis() {
                    if (loadMagnitudeItem.sliderVisible) {
                        for (var i = 1; i < loadMagnitudeItem.loadHelperData.loadStepFunction.length - 1; i++) {
                            if (loadMagnitudeItem.loadHelperData.loadStepFunction[i] === loadMagnitudeItem.sliderValue) {
                                loadHelperImage.source = imageData(loadMagnitudeItem.loadHelperData.imageLocation)
                                return true;
                            }
                        }
                    }
                    return false;
                }

                function imageData(image) {
                    if (selectLoadButton.checked) {
                        for (var i = 1; i < loadMagnitudeItem.loadHelperData.loadStepFunction.length - 1; i++) {
                            if (loadMagnitudeItem.loadHelperData.loadStepFunction[i] === loadMagnitudeItem.sliderValue) {
                                return image[i - 1];
                            }
                        }
                    }
                    return "";
                }

                color: UM.Theme.getColor("main_background")
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("lining")

                anchors {
                    top: faceDialog.top
                    left: loadColumn.right
                    leftMargin: UM.Theme.getSize("default_margin").width
                }
                radius: UM.Theme.getSize("default_radius").width

                height: contentRectangle.height + topDragArea.height - UM.Theme.getSize("default_lining").width
                width: contentRectangle.width
                visible: isVis()

                z: loadColumn.z - 1

                Label {
                    id: topText
                    anchors {
                        top:parent.top
                        topMargin: UM.Theme.getSize("default_margin").width
                        left: parent.left
                        leftMargin: UM.Theme.getSize("default_margin").width
                    }
                    renderType: Text.NativeRendering
                    font: UM.Theme.getFont("default_bold")
                    color: UM.Theme.getColor("text")
                    text: "Example:"
                }

                Image {
                    id: loadHelperImage
                    mipmap: true

                    anchors {
                        top: topText.bottom
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                        left: parent.left
                        leftMargin: UM.Theme.getSize("default_margin").width
                        bottom: loadHelperSeparator.top
                    }

                    fillMode: Image.PreserveAspectFit
                    source: loadHelperImageRect.imageData(loadMagnitudeItem.loadHelperData.imageLocation)
                }

                Rectangle {
                    id: loadHelperSeparator
                    border.color: UM.Theme.getColor("lining")
                    color: UM.Theme.getColor("lining")

                    anchors {
                        bottom: imageType.top
                        bottomMargin: UM.Theme.getSize("default_margin").width / 2
                        right: parent.right
                        left: parent.left
                    }

                    width: parent.width
                    height: 1
                }

                Text {
                    id: imageType

                    anchors {
                        bottom: weight.top
                        topMargin: UM.Theme.getSize("default_margin").width / 2
                        left: parent.left
                        leftMargin: UM.Theme.getSize("default_margin").width
                    }

                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                    text: loadHelperImageRect.imageData(loadMagnitudeItem.loadHelperData.imageType)
                }

                Text {
                    id: weight

                    anchors {
                        bottom: parent.bottom
                        bottomMargin: UM.Theme.getSize("default_margin").width / 2
                        topMargin: UM.Theme.getSize("default_margin").width / 2
                        left: parent.left
                        leftMargin: UM.Theme.getSize("default_margin").width
                    }

                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                    text: loadHelperImageRect.imageData(loadMagnitudeItem.loadHelperData.loadHelperEquivalentValue)
                }
            }
        }
    }
}

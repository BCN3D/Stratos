import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Controls 2.0 as QTC
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

import SmartSlice 1.0  as SmartSlice

Item {
    id: base

    property var loadChecked: false
    property var model
    property alias comboModel: comboDialogType.model

    property var tooltipLocations: UM.Controller.activeStage.proxy.tooltipLocations

    height: loadChecked ? bcType.height + iconsColumn.height : labelLoadDialogType.height + surfaceFilterLabel.height + UM.Theme.getSize("default_margin").width
    width: parent.width

    function update() {

        if (base.model.surfaceType === 1) {
            flatFace.color = UM.Theme.getColor("action_button_text");
            concaveFace.color = UM.Theme.getColor("text_inactive");
            convexFace.color = UM.Theme.getColor("text_inactive");
        } else if (base.model.surfaceType === 2) {
            flatFace.color = UM.Theme.getColor("text_inactive");
            concaveFace.color = UM.Theme.getColor("action_button_text");
            convexFace.color = UM.Theme.getColor("text_inactive");
        } else if (base.model.surfaceType === 3) {
            flatFace.color = UM.Theme.getColor("text_inactive");
            concaveFace.color = UM.Theme.getColor("text_inactive");
            convexFace.color = UM.Theme.getColor("action_button_text");
        }

        if (base.model.loadType === 1) {
            normalLoad.color = UM.Theme.getColor("action_button_text");
            parallelLoad.color = UM.Theme.getColor("text_inactive");
        } else {
            normalLoad.color = UM.Theme.getColor("text_inactive");
            parallelLoad.color = UM.Theme.getColor("action_button_text");
        }

        if (base.model.loadDirection) {
            flipIcon.color = UM.Theme.getColor("action_button_text");
        } else {
            flipIcon.color = UM.Theme.getColor("text_inactive");
        }
    }

    Row {
        id: bcType

        spacing: UM.Theme.getSize("default_margin").width

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            leftMargin: UM.Theme.getSize("default_margin").width
            rightMargin: UM.Theme.getSize("default_margin").width
        }

        Label {
            id: labelLoadDialogType

            height: UM.Theme.getSize("section").height
            verticalAlignment: Text.AlignVCenter

            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            text: "Type:"
        }

        Cura.ComboBox {
            id: comboDialogType

            width: parent.width - labelLoadDialogType.width - UM.Theme.getSize("default_margin").width
            height: UM.Theme.getSize("section").height
            anchors.verticalCenter: parent.verticalCenter

            textRole: "key"
        }
    }

    Column {
        id: labelsColumn

        anchors {
            top: bcType.bottom
            left: parent.left
            margins: UM.Theme.getSize("default_margin").width
        }

        width: childrenRect.width
        height: childrenRect.height
        spacing: UM.Theme.getSize("default_margin").width

        Label {
            id: surfaceFilterLabel

            height: UM.Theme.getSize("section").height

            verticalAlignment: Text.AlignVCenter

            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            text: "Surface Selection:"
        }

        Label {
            id: labelLoadDialogDirection

            visible: base.loadChecked

            height: UM.Theme.getSize("section").height

            verticalAlignment: Text.AlignVCenter

            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            text: "Load Direction:"
        }

    }

    Column {
        id: iconsColumn

        anchors {
            top: bcType.bottom
            left: labelsColumn.right
            right: parent.right
            topMargin: UM.Theme.getSize("default_margin").width
            leftMargin: UM.Theme.getSize("default_margin").width
            rightMargin: UM.Theme.getSize("default_margin").width
        }

        height: childrenRect.height
        spacing: UM.Theme.getSize("default_margin").width

        Row {
            id: surfaceRow

            width: childrenRect.width
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").width

            SmartSlice.HoverableButton {
                id: flatFace
                width: height
                height: UM.Theme.getSize("section").height

                iconSource: "media/flat.png"
                visible: true
                enabled: true

                color: base.model.surfaceType  != 1 ? UM.Theme.getColor("text_inactive") : UM.Theme.getColor("action_button_text")

                hoverColor: UM.Theme.getColor("setting_category_hover_border")

                onClicked: {
                    base.model.surfaceType = 1;
                    base.update();
                }

                tooltipHeader: catalog.i18nc("@textfp", "Flat Surface Selection")
                tooltipDescription: catalog.i18nc("@textfp", "Select flat surfaces.")

                tooltipTarget.x: 3 * width + 3 * surfaceRow.spacing
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]
            }

            SmartSlice.HoverableButton {
                id: concaveFace
                width: height
                height: UM.Theme.getSize("section").height

                iconSource: "media/concave.png"
                visible: true
                enabled: true

                color: base.model.surfaceType  != 2 ? UM.Theme.getColor("text_inactive") : UM.Theme.getColor("action_button_text")

                hoverColor: UM.Theme.getColor("setting_category_hover_border")

                onClicked: {
                    base.model.surfaceType = 2;
                    base.update();
                }

                tooltipHeader: catalog.i18nc("@textfp", "Concave Surface Selection")
                tooltipDescription: catalog.i18nc("@textfp", "Select the interior of rounded surfaces. "
                    + "For load surfaces, the surface must have a constant axis of revolution (cylindrical).")

                tooltipTarget.x: 2 * width + 2 * surfaceRow.spacing
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]
            }

            SmartSlice.HoverableButton {
                id: convexFace
                width: height
                height: UM.Theme.getSize("section").height

                iconSource: "media/convex.png"
                visible: true
                enabled: true

                color: base.model.surfaceType  != 3 ? UM.Theme.getColor("text_inactive") : UM.Theme.getColor("action_button_text")

                hoverColor: UM.Theme.getColor("setting_category_hover_border")

                onClicked: {
                    base.model.surfaceType = 3;
                    base.update();
                }

                tooltipHeader: catalog.i18nc("@textfp", "Convex Surface Selection")
                tooltipDescription: catalog.i18nc("@textfp", "Select the exterior of rounded surfaces. "
                    + "For load surfaces, the surface must have a constant axis of revolution (cylindrical).")

                tooltipTarget.x: width + surfaceRow.spacing
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]
            }
        }

        Row {
            id: loadDirectionRow
            visible: base.loadChecked

            width: childrenRect.width
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").width

            SmartSlice.HoverableButton {
                id: normalLoad
                width: height
                height: UM.Theme.getSize("section").height

                iconSource: "media/load_normal.png"
                visible: true
                enabled: true

                color: base.model.loadType  != 1 ? UM.Theme.getColor("text_inactive") : UM.Theme.getColor("action_button_text")

                hoverColor: UM.Theme.getColor("setting_category_hover_border")

                onClicked: {
                    base.model.loadType = 1;
                    base.update();
                }

                tooltipHeader: catalog.i18nc("@textfp", "Normal Load Direction")
                tooltipDescription: catalog.i18nc("@textfp", "For flat surface selection this will place the load arrow perpendicular to the surface. "
                    + "For either concave or convex surface selection this will place the load arrow perpendicular to the central axis of the cylindrical object.")

                tooltipTarget.x: 3 * width + 3 * loadDirectionRow.spacing
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]
            }

            SmartSlice.HoverableButton {
                id: parallelLoad
                width: height
                height: UM.Theme.getSize("section").height

                iconSource: "media/load_parallel.png"
                visible: true
                enabled: true

                color: base.model.loadType  != 2 ? UM.Theme.getColor("text_inactive") : UM.Theme.getColor("action_button_text")

                hoverColor: UM.Theme.getColor("setting_category_hover_border")

                onClicked: {
                    base.model.loadType = 2;
                    base.update();
                }

                tooltipHeader: catalog.i18nc("@textfp", "Parallel Load Direction")
                tooltipDescription: catalog.i18nc("@textfp", "For flat surface selection this will place the load arrow parallel to the surface. "
                    + "For either concave or convex surface selection this will place the load arrow parallel to the central axis of the cylindrical object.")

                tooltipTarget.x: 2 * width + 2 * loadDirectionRow.spacing
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]
            }
        }

        Row {
            id: flipRow
            visible: base.loadChecked

            width: childrenRect.width
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").width

            SmartSlice.HoverableButton {
                id: flipIcon
                width: height
                height: UM.Theme.getSize("section").height

                iconSource: "media/flip.png"
                visible: true
                enabled: true

                color: base.model.loadDirection  == false ? UM.Theme.getColor("text_inactive") : UM.Theme.getColor("action_button_text")

                hoverColor: UM.Theme.getColor("setting_category_hover_border")

                onClicked: {
                    base.model.loadDirection = !base.model.loadDirection;
                    base.update();
                }

                tooltipHeader: catalog.i18nc("@textfp", "Flip Arrow Direction")
                tooltipDescription: catalog.i18nc("@textfp", "Flip the tail and head of the load arrow.")

                tooltipTarget.x: 3 * width + 3 * flipRow.spacing
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]
            }
        }
    }
}

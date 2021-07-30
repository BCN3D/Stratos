import QtQuick 2.4
import QtQuick.Controls 1.2
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

    height: loadChecked ? contentColumn.height : bcType.height + surfaceSelectionLabel.height + surfaceSelection.height + angleSliderItem.height + 3 * UM.Theme.getSize("default_margin").width
    width: parent.width

    function update() {
        selectionCriteriaComboBox.currentIndex = model.surfaceSelectionCriteria - 1;
        angleSlider.value = model.surfaceSelectionAngle;

        xDirectionEntry.text = model.enableLoad ? model.loadXDirection : "";
        yDirectionEntry.text = model.enableLoad ? model.loadYDirection : "";
        zDirectionEntry.text = model.enableLoad ? model.loadZDirection : "";
    }

    Column {
        id: contentColumn

        width: parent.width
        height: childrenRect.height

        spacing: UM.Theme.getSize("default_margin").width

        Row {
            id: bcType

            spacing: UM.Theme.getSize("default_margin").width

            anchors {
                left: parent.left
                right: parent.right
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

                height: UM.Theme.getSize("section").height

                width: parent.width - labelLoadDialogType.width - UM.Theme.getSize("default_margin").width
                anchors.verticalCenter: parent.verticalCenter

                textRole: "key"
            }
        }

        Label {
            id: surfaceSelectionLabel

            height: UM.Theme.getSize("section").height
            verticalAlignment: Text.AlignVCenter

            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            text: "Surface Selection:"
        }

        Row {
            id: surfaceSelection

            anchors {
                left: parent.left
                right: parent.right
            }

            height: childrenRect.height

            spacing: UM.Theme.getSize("default_margin").width

            Column {
                id: selectionLabels

                anchors {
                    leftMargin: UM.Theme.getSize("default_margin").width
                }

                width: childrenRect.width
                height: childrenRect.height

                spacing: UM.Theme.getSize("default_margin").width

                Label {
                    id: selectionCriteriaLabel

                    height: UM.Theme.getSize("section").height
                    verticalAlignment: Text.AlignVCenter

                    leftPadding: UM.Theme.getSize("default_margin").width

                    font: UM.Theme.getFont("default_bold")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering

                    text: "Selection Criteria:"
                }

                Label {
                    id: angleLabel

                    height: UM.Theme.getSize("section").height
                    verticalAlignment: Text.AlignVCenter

                    leftPadding: UM.Theme.getSize("default_margin").width

                    font: UM.Theme.getFont("default_bold")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering

                    text: "Selection Angle:"
                }
            }

            Column {
                id: selectionInputs

                anchors {
                    rightMargin: UM.Theme.getSize("default_margin").width
                }

                width: parent.width - selectionLabels.width - UM.Theme.getSize("default_margin").width
                height: childrenRect.height

                spacing: UM.Theme.getSize("default_margin").width

                SmartSlice.HoverableComboBox {
                    id: selectionCriteriaComboBox

                    width: parent.width

                    model: ListModel {
                        ListElement { key: "Selection"; value: 1 }
                        ListElement { key: "Neighbors"; value: 2 }
                    }

                    tooltipHeaders: [
                        catalog.i18nc("@textfp", "Measure from Selected Point"),
                        catalog.i18nc("@textfp", "Measure from Neighbors")
                    ]
                    tooltipDescriptions: [
                        catalog.i18nc("@textfp", "Measure surface angles from the selection point on the model. "
                            + "This will typically select less surface area and provide more control for selecting "
                            + "sub-surface areas on curved components."),
                        catalog.i18nc("@textfp", "Measure surface angles from neighboring points on the model. "
                            + "This will typically select more surface area and provide less control for selecting "
                            + "sub-surface areas on curved components.")
                    ]

                    tooltipTarget.x: width + UM.Theme.getSize("default_margin").width
                    tooltipTarget.y: 0.5 * height
                    tooltipLocation: base.tooltipLocations["right"]

                    onActivated: {
                        base.model.surfaceSelectionCriteria = model.get(currentIndex).value
                    }
                }

                SmartSlice.HoverableTextField {
                    id: angleEntry

                    width: parent.width

                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                    text: angleSlider.value

                    tooltipHeader: catalog.i18nc("@textfp", "Selection Angle")
                    tooltipDescription: catalog.i18nc("@textfp", "The angle to use when selecting surfaces.")

                    tooltipTarget.x: width + UM.Theme.getSize("default_margin").width
                    tooltipTarget.y: 0.5 * height
                    tooltipLocation: base.tooltipLocations["right"]

                    unit: "°"

                    onTextChanged: {
                        var value = parseFloat(text);
                        if (value >= angleSlider.minimumValue) {
                            if (value <= angleSlider.maximumValue) {
                                angleSlider.value = value;
                            } else {
                                angleSlider.value = angleSlider.maximumValue;
                            }
                        } else {
                            angleSlider.value = angleSlider.minimumValue;
                        }
                    }
                }
            }
        }

        Item {
            id: angleSliderItem

            anchors {
                left: parent.left
                right: parent.right
                topMargin: UM.Theme.getSize("default_margin").width
            }

            height: childrenRect.height

            Slider {
                id: angleSlider
                anchors.top: parent.top
                height: UM.Theme.getSize("print_setup_slider_handle").height // The handle is the widest element of the slider
                width: parent.width

                minimumValue: 1.0
                maximumValue: 180.0
                stepSize: 1
                tickmarksEnabled: false
                activeFocusOnPress: true

                enabled: true
                value: model.surfaceSelectionAngle

                updateValueWhileDragging: false

                style: SliderStyle {
                    //Draw line
                    groove: Item {
                        Rectangle {
                            height: UM.Theme.getSize("print_setup_slider_groove").height
                            width: parent.width - UM.Theme.getSize("print_setup_slider_handle").width
                            color: UM.Theme.getColor("quality_slider_available")
                            anchors {
                                horizontalCenter: parent.horizontalCenter
                                verticalCenter: parent.verticalCenter
                            }
                        }
                    }

                    handle: Rectangle {
                        id: handleButton
                        color: UM.Theme.getColor("primary")
                        implicitWidth: UM.Theme.getSize("print_setup_slider_handle").width
                        implicitHeight: implicitWidth
                        radius: Math.round(implicitWidth / 2)
                    }
                }

                onValueChanged: {
                    model.surfaceSelectionAngle = value
                    angleEntry.text = value
                }
            }

            Label {
                id: angle_0
                anchors {
                    left: parent.left
                    top: angleSlider.bottom
                }

                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering

                text: "1°"
            }

            Label {
                id: angle_90
                anchors {
                    horizontalCenter: parent.horizontalCenter
                    top: angleSlider.bottom
                }

                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering

                text: "90°"
            }

            Label {
                id: angle_180
                anchors {
                    right: parent.right
                    top: angleSlider.bottom
                }

                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering

                text: "180°"
            }
        }

        Label {
            height: comboDialogType.height
            verticalAlignment: Text.AlignVCenter

            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            visible: loadChecked

            text: "Load Direction:"
        }

        Row {
            id: xDirection

            visible: loadChecked

            spacing: UM.Theme.getSize("default_margin").width

            anchors {
                left: parent.left
                right: parent.right
                leftMargin: UM.Theme.getSize("default_margin").width
            }

            width: parent.width

            Label {
                id: xDirectionLabel

                height: comboDialogType.height
                verticalAlignment: Text.AlignVCenter

                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("x_axis")
                renderType: Text.NativeRendering

                text: "X"
            }

            SmartSlice.HoverableTextField {
                id: xDirectionEntry

                readOnly: true

                width: parent.width - xDirectionLabel.width - UM.Theme.getSize("default_margin").width

                inputMethodHints: Qt.ImhFormattedNumbersOnly
                text: enabled ? base.model.loadXDirection : ""

                tooltipHeader: catalog.i18nc("@textfp", "Load X Direction Component (Not Editable)")
                tooltipDescription: catalog.i18nc("@textfp", "The X direction component of the applied load vector in reference to the global coordinate system. "
                    + "This does not include the magnitude.")

                tooltipTarget.x: width + UM.Theme.getSize("default_margin").width
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]

                unit: ""

                // onTextChanged: {
                //     var value = parseFloat(text);
                //     base.model.loadXDirection = value;
                // }

                onEditingFinished: {
                    var value = parseFloat(text);
                    base.model.loadXDirection = value;
                    base.update();
                }
            }
        }

        Row {
            id: yDirection

            visible: loadChecked

            spacing: UM.Theme.getSize("default_margin").width

            anchors {
                left: parent.left
                right: parent.right
                leftMargin: UM.Theme.getSize("default_margin").width
            }

            width: parent.width

            Label {
                id: yDirectionLabel

                height: comboDialogType.height
                verticalAlignment: Text.AlignVCenter

                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("z_axis")
                renderType: Text.NativeRendering

                text: "Y"
            }

            SmartSlice.HoverableTextField {
                id: yDirectionEntry

                readOnly: true

                width: parent.width - yDirectionLabel.width - UM.Theme.getSize("default_margin").width

                inputMethodHints: Qt.ImhFormattedNumbersOnly
                text: enabled ? base.model.loadYDirection : ""

                tooltipHeader: catalog.i18nc("@textfp", "Load Y Direction Component (Not Editable)")
                tooltipDescription: catalog.i18nc("@textfp", "The Y direction component of the applied load vector in reference to the global coordinate system. "
                    + "This does not include the magnitude.")

                tooltipTarget.x: width + UM.Theme.getSize("default_margin").width
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]

                unit: ""

                onEditingFinished: {
                    var value = parseFloat(text);
                    base.model.loadYDirection = value;
                    base.update();
                }
            }
        }

        Row {
            id: zDirection

            visible: loadChecked

            spacing: UM.Theme.getSize("default_margin").width

            anchors {
                left: parent.left
                right: parent.right
                leftMargin: UM.Theme.getSize("default_margin").width
            }

            width: parent.width

            Label {
                id: zDirectionLabel

                height: comboDialogType.height
                verticalAlignment: Text.AlignVCenter

                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("y_axis")
                renderType: Text.NativeRendering

                text: "Z"
            }

            SmartSlice.HoverableTextField {
                id: zDirectionEntry

                readOnly: true

                width: parent.width - zDirectionLabel.width - UM.Theme.getSize("default_margin").width

                inputMethodHints: Qt.ImhFormattedNumbersOnly
                text: enabled ? base.model.loadZDirection : ""

                tooltipHeader: catalog.i18nc("@textfp", "Load Z Direction Component (Not Editable)")
                tooltipDescription: catalog.i18nc("@textfp", "The Z direction component of the applied load vector in reference to the global coordinate system. "
                    + "This does not include the magnitude.")

                tooltipTarget.x: width + UM.Theme.getSize("default_margin").width
                tooltipTarget.y: 0.5 * height
                tooltipLocation: base.tooltipLocations["right"]

                unit: ""

                // onTextChanged: {
                //     var value = parseFloat(text);
                //     base.model.loadZDirection = value;
                // }

                onEditingFinished: {
                    var value = parseFloat(text);
                    base.model.loadZDirection = value;
                    base.update();
                }
            }
        }
    }
}

import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Controls 2.0 as QTC
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import SmartSlice 1.0 as SmartSlice

Item {
    id: base

    property alias magnitude: magnitudeEntry.text
    property alias sliderValue: loadHelper.value
    property alias sliderVisible: sliderRect.visible
    property var model
    property var tooltipLocations: UM.Controller.activeStage.proxy.tooltipLocations

    height: {
        if (visible) {
            if (sliderRect.visible) {
                return magnitudeLabel.height + magnitudeEntry.height + sliderRect.height + 4 * UM.Theme.getSize("default_margin").width
            } else {
                return magnitudeLabel.height + magnitudeEntry.height + 2 * UM.Theme.getSize("default_margin").width
            }
        }
        return 0
    }

    property var loadHelperData: {
        "maxValue": 1500,
        "stepSize": 300,
        "textLoadDialogConverter": [0, 150, 250, 500, 1500],
        "textLoadMultiplier": [2.4, 2.4, 1.2, .6],
        "textLoadOffset": [0, 0, 300, 600],
        "loadStepFunction": [0, 300, 600, 900, 1200, 1500],
        "loadStepDivision": [1, 2.4, 2.4, 1.8, 1.2, 1],
        "imageLocation": ["media/Toddler.png", "media/Child.png", "media/Teenager.png", "media/Adult.png"],
        "imageType": ["<b>Toddler</b>", "<b>Young Child</b>", "<b>Teenager</b>", "<b>Adult</b>"],
        "loadHelperEquivalentValue": ["125 N (~30 lbs)", "250 N (~60 lbs)", "500 N (~110 lbs)", "1000 N (~225 lbs)"]
    }


    Column {
        id: contentColumn

        height: childrenRect.height
        width: parent.width

        spacing: UM.Theme.getSize("default_margin").width

        Label {
            id: magnitudeLabel

            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            text: "Load Magnitude:"
        }

        SmartSlice.HoverableTextField {
            id: magnitudeEntry

            anchors {
                left: parent.left
                right: parent.right
                topMargin: UM.Theme.getSize("default_margin").height
                leftMargin: UM.Theme.getSize("default_margin").width
            }

            function loadHelperStep(value) {
                for (var i = 0; i < loadHelperData.textLoadDialogConverter.length - 1; i++){
                    if (value >= loadHelperData.textLoadDialogConverter[i] && value <= loadHelperData.textLoadDialogConverter[i + 1]) {
                        return value * loadHelperData.textLoadMultiplier[i] + loadHelperData.textLoadOffset[i];
                    }
                }
                return value;
            }

            onTextChanged: {
                var value = parseFloat(text);
                if (value >= 0.0) {
                    base.model.loadMagnitude = value;
                    loadHelper.value = loadHelperStep(value);
                }
            }

            onEditingFinished: {
                var value = parseFloat(text);
                base.model.loadMagnitude = value;
            }

            validator: DoubleValidator {bottom: 0.0}
            inputMethodHints: Qt.ImhFormattedNumbersOnly
            text:  base.model.loadMagnitude

            tooltipHeader: catalog.i18nc("@textfp", "Load Magnitude")
            tooltipDescription: {
                if (sliderRect.visible) {
                    return catalog.i18nc("@textfp", "The absolute value of the applied load on the selected surface in the prescribed direction. "
                        + "The load is distributed over the selected surface, and the pictures on the slider provide context to various load magnitudes.")
                }
                return catalog.i18nc("@textfp", "The absolute value of the applied load on the selected surface in the prescribed direction. "
                        + "The load is distributed over the selected surface.")
            }

            tooltipTarget.x: width + UM.Theme.getSize("default_margin").width
            tooltipTarget.y: 0.5 * height
            tooltipLocation: base.tooltipLocations["right"]

            unit: "[N]"
        }

        Rectangle {
            id: sliderRect

            anchors {
                left: parent.left
                right: parent.right
                top: magnitudeEntry.bottom
                topMargin: UM.Theme.getSize("default_margin").width
            }

            QTC.Slider {
                id: loadHelper
                from: 0
                to: loadHelperData.maxValue
                stepSize: 1

                anchors {
                    left: parent.left
                    right: parent.right
                    topMargin: UM.Theme.getSize("default_margin").width
                }


                background:
                    Rectangle {
                        x: 0
                        y: loadHelper.topPadding + loadHelper.availableHeight / 2 - height / 2
                        height: UM.Theme.getSize("print_setup_slider_groove").height
                        width: loadHelper.width - UM.Theme.getSize("print_setup_slider_handle").width
                        color: loadHelper.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                        anchors {
                            horizontalCenter: parent.horizontalCenter
                            verticalCenter: parent.verticalCenter
                        }

                    Repeater {
                        id: tickmarks
                        model: loadHelperData.maxValue / loadHelperData.stepSize -1
                        Rectangle {
                            function indexHelper(index) {
                                if (index === 3) {
                                    return loadHelper.availableWidth * (index + 1) / (tickmarks.model + 1) - 3;
                                };
                                return loadHelper.availableWidth * (index + 1) / (tickmarks.model + 1);
                            }
                            x: indexHelper(index)
                            y: loadHelper.topPadding + loadHelper.availableHeight / 2 - height / 2
                            color: loadHelper.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            implicitWidth: UM.Theme.getSize("print_setup_slider_tickmarks").width
                            implicitHeight: UM.Theme.getSize("print_setup_slider_tickmarks").height
                            anchors.verticalCenter: parent.verticalCenter
                            radius: Math.round(implicitWidth / 2)
                        }
                    }
                }

                handle: Rectangle {
                    id: handleButton
                    x: loadHelper.leftPadding + loadHelper.visualPosition * (loadHelper.availableWidth - width)
                    y: loadHelper.topPadding + loadHelper.availableHeight / 2 - height / 2
                    color: loadHelper.enabled ? UM.Theme.getColor("primary") : UM.Theme.getColor("quality_slider_unavailable")
                    implicitWidth: UM.Theme.getSize("print_setup_slider_handle").width
                    implicitHeight: implicitWidth
                    radius: Math.round(implicitWidth)
                }

                onMoved: {
                    function loadMagnitudeStep(value){
                        for (var i = 0; i < loadHelperData.loadStepFunction.length; i++) {
                            if (loadHelperData.loadStepFunction[i] === value) {
                                return value / loadHelperData.loadStepDivision[i];
                            }
                        }
                    }
                    var roundedSliderValue = Math.round(loadHelper.value / loadHelperData.stepSize) * loadHelperData.stepSize;
                    loadHelper.value = roundedSliderValue;
                    magnitudeEntry.text = loadMagnitudeStep(roundedSliderValue);
                }
            }
        }
    }
}
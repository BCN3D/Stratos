import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

import SmartSlice 1.0  as SmartSlice

Item {
    id: requirements

    width: textfields.width
    height: textfields.height
    UM.I18nCatalog { id: catalog; name: "smartslice"}

    property string targetSafetyFactorText
    property var tooltipLocations: UM.Controller.activeStage.proxy.tooltipLocations

    Grid {
        id: textfields

        anchors.top: parent.top

        columns: 2
        flow: Grid.TopToBottom
        spacing: Math.round(UM.Theme.getSize("default_margin").width / 2)

        Label {
            height: UM.Theme.getSize("setting_control").height

            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            text: catalog.i18nc("@label", "Factor of Safety")
            verticalAlignment: TextInput.AlignVCenter
        }

        Label {
            height: UM.Theme.getSize("setting_control").height

            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            text: catalog.i18nc("@label", "Max Deflection")
            verticalAlignment: TextInput.AlignVCenter
        }

        SmartSlice.HoverableTextField {
            id: valueSafetyFactor
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height

            validator: DoubleValidator {bottom: 0.0}

            onTextChanged: {
                var value = parseFloat(text)
                if (value >= 1.0) {
                    UM.ActiveTool.setProperty("TargetSafetyFactor", value)
                }
            }

            onEditingFinished: {
                var value = parseFloat(text)
                if (value >= 1.0) {
                    UM.ActiveTool.setProperty("TargetSafetyFactor", value)
                } else {
                    text = "1"
                }
            }

            tooltipHeader: catalog.i18nc("@textfp", "Factor of Safety")
            tooltipDescription: catalog.i18nc("@textfp", "This value is related to the uncertainty of the applied load. "
                    + "It represents the multiple of the applied load the part should handle before it begins to permanently deform, "
                    + "which allows the user to be confident the part will not fail. Typical values are 1.5 to 3.")

            tooltipTarget.x: width + Math.round(UM.Theme.getSize("default_margin").width)
            tooltipTarget.y: 0.5 * height
            tooltipLocation: faceDialog.tooltipLocations["right"]

            inputMethodHints: Qt.ImhFormattedNumbersOnly
            unit: " "
        }

        SmartSlice.HoverableTextField {
            id: valueMaxDeflect
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height

            onTextChanged: {
                var value = parseFloat(text)
                if (value > 0.) {
                    UM.ActiveTool.setProperty("MaxDisplacement", value)
                }
            }

            tooltipHeader: catalog.i18nc("@textfp", "Maximum Displacement")
            tooltipDescription: catalog.i18nc("@textfp", "This value indicates how stiff the part needs to be. "
                    + "It represents the maximum amount the part can deflect (or move) under the applied loads in order to stay within tolerance.")

            tooltipTarget.x: width + Math.round(UM.Theme.getSize("default_margin").width)
            tooltipTarget.y: 0.5 * height
            tooltipLocation: faceDialog.tooltipLocations["right"]

            validator: DoubleValidator {bottom: 0.0}
            inputMethodHints: Qt.ImhFormattedNumbersOnly

            unit: "[mm]"
        }

        Binding {
            target: valueSafetyFactor
            property: "text"
            value: UM.ActiveTool.properties.getValue("TargetSafetyFactor")
        }

        Binding {
            target: valueMaxDeflect
            property: "text"
            value: UM.ActiveTool.properties.getValue("MaxDisplacement")
        }

        Connections {
            target: UM.Controller.activeStage.proxy
            onUpdateTargetUi: {
                UM.ActiveTool.forceUpdate()
                valueSafetyFactor.text = UM.ActiveTool.properties.getValue("TargetSafetyFactor")
                valueMaxDeflect.text = UM.ActiveTool.properties.getValue("MaxDisplacement")
            }
        }
    }
}

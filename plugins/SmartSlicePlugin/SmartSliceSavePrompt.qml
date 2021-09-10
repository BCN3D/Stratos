import QtQuick 2.7
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2

import UM 1.2 as UM
import Cura 1.1 as Cura

UM.Dialog {
    id: saveDialog

    property var proxy: UM.Controller.activeStage.proxy

    title: "SmartSlice Warning"

    width: Math.floor(screenScaleFactor * 300)
    height: Math.floor(screenScaleFactor * 150)

    minimumWidth: width;
    maximumWidth: width;

    minimumHeight: height;
    maximumHeight: height;

    x: 0.5 * (CuraApplication.appWidth() - width)
    y: 0.5 * (CuraApplication.appHeight() - height)

    closeOnAccept: false

    Column {

        UM.I18nCatalog{id: catalog; name: "smartslice"}
        anchors.fill: parent
        anchors.margins: UM.Theme.getSize("default_margin").width

        spacing: UM.Theme.getSize("default_margin").height

        Label {
            id: resultsLabel

            width: parent.width

            Layout.alignment: Qt.AlignLeft

            font: UM.Theme.getFont("default")

            text: 'You have unsaved SmartSlice results!'
        }

        Label {
            id: saveLabel

            width: parent.width

            Layout.alignment: Qt.AlignLeft

            font: UM.Theme.getFont("default")

            text: 'Would you like to save your results?'
        }
    }

    Item {
        id: buttonRow

        width: parent.width

        anchors {
            bottom: parent.bottom
            right: parent.right
            left: parent.left
            rightMargin: UM.Theme.getSize("default_margin").width
            leftMargin: UM.Theme.getSize("default_margin").width
        }

        Row {
            id: buttons

            anchors {
                bottom: parent.bottom
                right: parent.right
            }

            spacing: UM.Theme.getSize("default_margin").width

            Button {
                text: catalog.i18nc("@action:button", "Don't Save")
                onClicked: {
                    saveDialog.proxy.closeSavePromptClicked()
                }
            }

            Button {
                text: catalog.i18nc("@action:button", "Save")
                onClicked: {
                    saveDialog.proxy.savePromptClicked()
                }
            }
        }
    }
}



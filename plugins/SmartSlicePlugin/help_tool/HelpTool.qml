import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

import SmartSlice 1.0  as SmartSlice

Item {
    id: help

    height: childrenRect.height
    width: childrenRect.width
    UM.I18nCatalog { id: catalog; name: "smartslice"}

    property var proxy: UM.Controller.activeStage.proxy
    property var urlHandler: SmartSlice.URLHandler{}

    Column {
        spacing: Math.round(UM.Theme.getSize("default_margin").width)

        Label {
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            color: accountMouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_text")

            text: "My Account"

            MouseArea {
                id: accountMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: Qt.openUrlExternally(urlHandler.account)
            }
        }

        Label {
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            color: helpMouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_text")

            text: "Access Help"

            MouseArea {
                id: helpMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: Qt.openUrlExternally(urlHandler.help)
            }
        }

        Label {
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            color: tutorial1MouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_text")

            text: "Tutorials"

            MouseArea {
                id: tutorial1MouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    proxy.setIntroScreenVisibility(false)
                    proxy.setWelcomeScreenVisibility(true)
                }
            }
        }
    }
}

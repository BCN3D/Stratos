import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Row // Sync state icon + message
{
    property var syncState: Cura.API.account.syncState

    id: syncRow
    width: childrenRect.width
    height: childrenRect.height
    spacing: UM.Theme.getSize("narrow_margin").height

    states: [
        State
        {
            name: "idle"
            when: syncState == Cura.AccountSyncState.IDLE
            PropertyChanges { target: icon; source: UM.Theme.getIcon("update")}
        },
        State
        {
            name: "syncing"
            when: syncState == Cura.AccountSyncState.SYNCING
            PropertyChanges { target: icon; source: UM.Theme.getIcon("update") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Checking...")}
        },
        State
        {
            name: "up_to_date"
            when: syncState == Cura.AccountSyncState.SUCCESS
            PropertyChanges { target: icon; source: UM.Theme.getIcon("checked") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Account synced")}
        },
        State
        {
            name: "error"
            when: syncState == Cura.AccountSyncState.ERROR
            PropertyChanges { target: icon; source: UM.Theme.getIcon("warning_light") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Something went wrong...")}
        }
    ]

    UM.RecolorImage
    {
        id: icon
        width: 20 * screenScaleFactor
        height: width

        // source is determined by State
        color: UM.Theme.getColor("account_sync_state_icon")

        RotationAnimator
        {
            id: updateAnimator
            target: icon
            from: 0
            to: 360
            duration: 1000
            loops: Animation.Infinite
            running: syncState == Cura.AccountSyncState.SYNCING

            // reset rotation when stopped
            onRunningChanged: {
                if(!running)
                {
                    icon.rotation = 0
                }
            }
        }
    }

    Column
    {
        width: childrenRect.width
        height: childrenRect.height

        Label
        {
            id: stateLabel
            // text is determined by State
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
            width: contentWidth + UM.Theme.getSize("default_margin").height
            height: contentHeight
            verticalAlignment: Text.AlignVCenter
            visible: !Cura.API.account.manualSyncEnabled && !Cura.API.account.updatePackagesEnabled
        }

        Label
        {
            id: updatePackagesButton
            text: catalog.i18nc("@button", "Install pending updates")
            color: UM.Theme.getColor("text_link")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            height: contentHeight
            width: contentWidth + UM.Theme.getSize("default_margin").height
            visible: Cura.API.account.updatePackagesEnabled

            MouseArea
            {
                anchors.fill: parent
                onClicked: Cura.API.account.onUpdatePackagesClicked()
                hoverEnabled: true
                onEntered: updatePackagesButton.font.underline = true
                onExited: updatePackagesButton.font.underline = false
            }
        }

        Label
        {
            id: accountSyncButton
            text: catalog.i18nc("@button", "Check for account updates")
            color: UM.Theme.getColor("text_link")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            height: contentHeight
            width: contentWidth + UM.Theme.getSize("default_margin").height
            visible: Cura.API.account.manualSyncEnabled

            MouseArea
            {
                anchors.fill: parent
                onClicked: Cura.API.account.sync(true)
                hoverEnabled: true
                onEntered: accountSyncButton.font.underline = true
                onExited: accountSyncButton.font.underline = false
            }
        }
    }
}

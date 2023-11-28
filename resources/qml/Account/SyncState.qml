import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura

Row // Sync state icon + message
{
    property var syncState: Cura.API.account.syncState

    id: syncRow
    width: childrenRect.width
    height: childrenRect.height
    spacing: UM.Theme.getSize("narrow_margin").height

    // These are the enums from cura/API/account.py
    // somehow exposing these enums from python to QML doesn't work properly anymore
    property var _Cura_AccountSyncState_SYNCING: 0
    property var _Cura_AccountSyncState_SUCCESS: 1
    property var _Cura_AccountSyncState_ERROR: 2
    property var _Cura_AccountSyncState_IDLE: 3

    states: [
        State
        {
            name: "idle"
            when: syncState == _Cura_AccountSyncState_IDLE
            PropertyChanges { target: icon; source: UM.Theme.getIcon("ArrowDoubleCircleRight")}
        },
        State
        {
            name: "syncing"
            when: syncState == _Cura_AccountSyncState_SYNCING
            PropertyChanges { target: icon; source: UM.Theme.getIcon("ArrowDoubleCircleRight") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Checking...")}
        },
        State
        {
            name: "up_to_date"
            when: syncState == _Cura_AccountSyncState_SUCCESS
            PropertyChanges { target: icon; source: UM.Theme.getIcon("CheckCircle") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Account synced")}
        },
        State
        {
            name: "error"
            when: syncState == _Cura_AccountSyncState_ERROR
            PropertyChanges { target: icon; source: UM.Theme.getIcon("Warning") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Something went wrong...")}
        }
    ]

    UM.ColorImage
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

        UM.Label
        {
            id: stateLabel
            // text is determined by State
            font: UM.Theme.getFont("medium")
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            wrapMode: Text.NoWrap
            height: contentHeight
            visible: !Cura.API.account.manualSyncEnabled && !Cura.API.account.updatePackagesEnabled
        }

        UM.Label
        {
            id: updatePackagesButton
            text: catalog.i18nc("@button", "Install pending updates")
            color: UM.Theme.getColor("text_link")
            font: UM.Theme.getFont("medium")
            height: contentHeight
            wrapMode: Text.NoWrap
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

        UM.Label
        {
            id: accountSyncButton
            text: catalog.i18nc("@button", "Check for account updates")
            color: UM.Theme.getColor("text_link")
            font: UM.Theme.getFont("medium")
            wrapMode: Text.NoWrap
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

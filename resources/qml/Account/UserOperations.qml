// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Column
{
    spacing: UM.Theme.getSize("narrow_margin").height
    topPadding: UM.Theme.getSize("default_margin").height
    bottomPadding: UM.Theme.getSize("default_margin").height
    width: childrenRect.width

    Item
    {
        id: accountInfo
        width: childrenRect.width
        height: childrenRect.height
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        AvatarImage
        {
            id: avatar
            anchors.verticalCenter: parent.verticalCenter

            width: UM.Theme.getSize("main_window_header").height
            height: UM.Theme.getSize("main_window_header").height

            source: profile["profile_image_url"] ? profile["profile_image_url"] : ""
            outlineColor: UM.Theme.getColor("main_background")
        }
        Rectangle
        {
            id: initialCircle
            width: avatar.width
            height: avatar.height
            radius: width
            anchors.verticalCenter: parent.verticalCenter
            color: UM.Theme.getColor("action_button_disabled")
            visible: !avatar.hasAvatar
            Label
            {
                id: initialLabel
                anchors.centerIn: parent
                text: profile["username"].charAt(0).toUpperCase()
                font: UM.Theme.getFont("large_bold")
                color: UM.Theme.getColor("text")
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                renderType: Text.NativeRendering
            }
        }

        Column
        {
            anchors.left: avatar.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("narrow_margin").height
            width: childrenRect.width
            height: childrenRect.height
            Label
            {
                id: username
                renderType: Text.NativeRendering
                text: profile["username"] + "       "
                font: UM.Theme.getFont("large_bold")
                color: UM.Theme.getColor("text")
            }
        }
    }



    Cura.TertiaryButton
    {
        id: accountButton
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "BCN3D Cloud")
        onClicked: Qt.openUrlExternally("https://cloud.bcn3d.com/settings")
        fixedWidthMode: false
    }

    Rectangle
    {
        width: parent.width
        color: UM.Theme.getColor("lining")
        height: UM.Theme.getSize("default_lining").height
    }

    Cura.TertiaryButton
    {
        id: signOutButton
        onClicked: this.signOut()
        text: catalog.i18nc("@button", "Sign Out")

        function signOut() {
            var success = Cura.AuthenticationService.signOut()
            if (success) {
                popup.close()
            }
        }
    }
}

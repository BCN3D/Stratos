// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura

import "../components"


Column
{
    id: welcomePage
    spacing: UM.Theme.getSize("wide_margin").height
    width: parent.width
    height: childrenRect.height
    anchors.centerIn: parent

    Image
    {
        id: profileImage
        fillMode: Image.PreserveAspectFit
        source: Qt.resolvedUrl("../images/backup.svg")
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.round(parent.width / 4)
    }

    UM.Label
    {
        id: welcomeTextLabel
        text: catalog.i18nc("@description", "Backup and synchronize your Cura settings.")
        width: Math.round(parent.width / 2)
        horizontalAlignment: Text.AlignHCenter
        anchors.horizontalCenter: parent.horizontalCenter
        wrapMode: Label.WordWrap
    }

    Cura.PrimaryButton
    {
        id: loginButton
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        anchors.horizontalCenter: parent.horizontalCenter
        text: catalog.i18nc("@button", "Sign in")
        onClicked: Cura.API.account.login()
        fixedWidthMode: true
    }
}


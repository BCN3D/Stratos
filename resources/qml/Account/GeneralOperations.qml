// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Column
{
    spacing: UM.Theme.getSize("default_margin").width
    padding: UM.Theme.getSize("default_margin").width
    Image
    {
        id: machinesImage
        anchors.horizontalCenter: parent.horizontalCenter
        source: UM.Theme.getImage("first_run_welcome_cura")
        horizontalAlignment: Image.AlignHCenter
        verticalAlignment: Image.AlignVCenter
    }

    Label
    {
        id: title
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
        text: catalog.i18nc("@label", "BCN3D Cloud Account")
        font: UM.Theme.getFont("large_bold")
        color: UM.Theme.getColor("text")
    }

    Label
    {
        id: generalInformation
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
        text: catalog.i18nc("@label", "Your key to connected 3D printing")
        font: UM.Theme.getFont("default_bold")
        color: UM.Theme.getColor("text")
        visible: false
    }

    Label
    {
        id: generalInformationPoints
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignLeft
        renderType: Text.NativeRendering
        text: catalog.i18nc("@text", "- Customize your experience with more print profiles and plugins\n- Stay flexible by syncing your setup and loading it anywhere\n- Increase efficiency with a remote workflow on BCN3D printers")
        lineHeight: 1.4
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        visible: false
    }

    // placeholder
    Label
    {
        text: " "
    }

    Item
    {
        height: 50
        width: 250
        anchors.horizontalCenter: parent.horizontalCenter
        TextField
        {
            id: email
            text: emailText
            anchors.horizontalCenter: parent.horizontalCenter
            placeholderText: catalog.i18nc("@text", "Email")
            onEditingFinished: {
                if (text != "") emailErrorVisible = false
                else emailErrorVisible = true
            }
        }
        Label
        {
            id: emailError
            anchors.left: email.left
            anchors.top: email.bottom
            horizontalAlignment: Text.AlignLeft
            text: catalog.i18nc("@text", "Email is required")
            color: "red"
            visible: emailErrorVisible
        }
    }

    Item
    {
        height: 50
        width: 50
        anchors.horizontalCenter: parent.horizontalCenter
        TextField
        {
            id: password
            text: passwordText
            anchors.horizontalCenter: parent.horizontalCenter
            placeholderText: catalog.i18nc("@text", "Password")
            echoMode: TextInput.Password
            onEditingFinished: {
                if (text != "") passwordErrorVisible = false
                else passwordErrorVisible = true
            }
        }
        Label
        {
            id: passwordError
            anchors.left: password.left
            anchors.top: password.bottom
            horizontalAlignment: Text.AlignLeft
            text: catalog.i18nc("@text", "Password is required")
            color: "red"
            visible: passwordErrorVisible
        }
    }

    Item
    {
        height: 12
        width: 50
        anchors.horizontalCenter: parent.horizontalCenter
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: signInStatusCode == 400 || signInStatusCode == 401 ? catalog.i18nc("@text", "Incorrect email or password") : signInStatusCode == -1 ? catalog.i18nc("@text", "Can't sign in. Check internet connection") : signInStatusCode == -2 ? catalog.i18nc("@text", "Can't sign in. Error loading api data"): catalog.i18nc("@text", "Can't sign in. Something went wrong")
            color: "red"
            visible: signInStatusCode != 200
        }
    }

    Cura.PrimaryButton
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Sign in")
        onClicked: this.signIn()
        fixedWidthMode: true

        function signIn() {
            signInStatusCode = Cura.AuthenticationService.signIn(email.text, password.text)
            if (signInStatusCode == 200) {
                popup.close()
            }
        }
    }

    Cura.SecondaryButton
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Create account")
        onClicked: Qt.openUrlExternally("https://cloud.bcn3d.com")
        fixedWidthMode: true
    }
}
// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Item
{
    property var profile: Cura.API.account.userProfile
    property bool loggedIn: Cura.API.account.isLoggedIn
    property var profileImage: Cura.API.account.profileImageUrl

    Loader
    {
        id: accountOperations
        anchors.centerIn: parent
        sourceComponent: loggedIn ? userOperations : generalOperations
    }

    Component
    {
        id: userOperations
        UserOperations { }
    }

    Component
    {
        id: generalOperations
        GeneralOperations { }
    }
}
// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.5 as UM

RowLayout
{
    id: detailsRow
    width: parent.width
    height: 40 * screenScaleFactor

    property alias iconSource: icon.source
    property alias label: detailName.text
    property alias value: detailValue.text

    UM.ColorImage
    {
        id: icon
        width: 18 * screenScaleFactor
        height: width
        source: ""
        color: UM.Theme.getColor("text")
    }

    UM.Label
    {
        id: detailName
        elide: Text.ElideRight
        Layout.minimumWidth: 50 * screenScaleFactor
        Layout.maximumWidth: 100 * screenScaleFactor
        Layout.fillWidth: true
    }

    UM.Label
    {
        id: detailValue
        elide: Text.ElideRight
        Layout.minimumWidth: 50 * screenScaleFactor
        Layout.maximumWidth: 100 * screenScaleFactor
        Layout.fillWidth: true
    }
}

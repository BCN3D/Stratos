// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2

import UM 1.4 as UM
import Cura 1.1 as Cura


Cura.ActionButton
{
    shadowEnabled: true
    shadowColor: enabled ? UM.Theme.getColor("secondary_button_shadow"): UM.Theme.getColor("action_button_disabled_shadow")
    color: "transparent"
    textColor: UM.Theme.getColor("text_link")
    outlineColor: "transparent"
    disabledColor: UM.Theme.getColor("action_button_disabled")
    textDisabledColor: UM.Theme.getColor("action_button_disabled_text")
    hoverColor: "transparent"
    underlineTextOnHover: true
}

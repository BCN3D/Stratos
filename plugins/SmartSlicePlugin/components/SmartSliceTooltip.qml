import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.0 as UM

UM.PointingRectangle {
    id: base
    width: UM.Theme.getSize("tooltip").width
    height: toolTipColumn.height
    color: UM.Theme.getColor("tooltip")

    arrowSize: UM.Theme.getSize("default_arrow").width

    opacity: 0

    Behavior on opacity {
        NumberAnimation {
            duration: 250;
        }
    }

    property alias header: headerLabel.text
    property alias description: descriptionLabel.text

    property var locations: UM.Controller.activeStage.proxy.tooltipLocations
    property var location: locations["right"]

    function show() {
        if (header != "" || description != "") {
            base.z = 100;
            base.opacity = 1;
        }
    }

    function hide() {
        base.opacity = 0;
    }

    function setPosition() {
        if (location == locations["left"]) {
            x = target.x - UM.Theme.getSize("default_arrow").width - width;
            y = target.y - 0.5 * UM.Theme.getSize("default_arrow").height - UM.Theme.getSize("tooltip_arrow_margins").height;
        } else if (location == locations["top"]) {
            x = target.x - width + 0.5 * UM.Theme.getSize("default_arrow").width + UM.Theme.getSize("tooltip_arrow_margins").width;
            y = target.y - UM.Theme.getSize("default_arrow").height - height;
        } else if (location == locations["bottom"]) {
            x = target.x - width + 0.5 * UM.Theme.getSize("default_arrow").width + UM.Theme.getSize("tooltip_arrow_margins").width;
            y = target.y + UM.Theme.getSize("default_arrow").height;
        } else {
            x = target.x + UM.Theme.getSize("default_arrow").width;
            y = target.y - 0.5 * UM.Theme.getSize("default_arrow").height - UM.Theme.getSize("tooltip_arrow_margins").height;
        }
    }

    Component.onCompleted: {
        setPosition();
    }

    Column {
        id: toolTipColumn

        width: parent.width

        spacing: UM.Theme.getSize("tooltip_margins").height

        topPadding: UM.Theme.getSize("tooltip_margins").height
        bottomPadding: UM.Theme.getSize("tooltip_margins").height

        leftPadding: UM.Theme.getSize("tooltip_margins").width
        rightPadding: UM.Theme.getSize("tooltip_margins").width

        height: {
            var h = headerLabel.height + 2 * UM.Theme.getSize("tooltip_margins").height
            if (descriptionLabel.text != "") {
                h += descriptionLabel.height + spacing
            }
            return h
        }

        Label {
            id: headerLabel

            width: parent.width - 2 * parent.leftPadding

            anchors {
                topMargin: UM.Theme.getSize("tooltip_margins").height
                leftMargin: UM.Theme.getSize("tooltip_margins").width
                rightMargin: UM.Theme.getSize("tooltip_margins").width
            }

            wrapMode: Text.Wrap
            textFormat: Text.RichText
            font: UM.Theme.getFont("default_bold")
            color: UM.Theme.getColor("tooltip_text")
            // renderType: Text.NativeRendering
        }

        Label {
            id: descriptionLabel

            width: parent.width - 2 * parent.leftPadding

            anchors {
                bottomMargin: UM.Theme.getSize("tooltip_margins").height
                leftMargin: UM.Theme.getSize("tooltip_margins").width
                rightMargin: UM.Theme.getSize("tooltip_margins").width
            }

            wrapMode: Text.Wrap
            textFormat: Text.RichText
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("tooltip_text")
            // renderType: Text.NativeRendering
        }
    }
}

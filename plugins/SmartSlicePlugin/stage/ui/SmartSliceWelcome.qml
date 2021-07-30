import QtQuick 2.10
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.4

import Cura 1.0 as Cura
import UM 1.2 as UM

import SmartSlice 1.0 as SmartSlice

MouseArea {
    id: welcome

    width: smartSliceMain.width
    height: smartSliceMain.height

    hoverEnabled: true
    preventStealing: true
    scrollGestureEnabled: false

    onClicked: {}
    onWheel: {}

    Item {

        property var minWidth: 0.60 * smartSliceMain.width
        property var maxWidth: 0.95 * smartSliceMain.width

        property var minHeight: 0.60 * smartSliceMain.height
        property var maxHeight: 0.95 * smartSliceMain.height

        property var newWidth: introAction.width + 2 * UM.Theme.getSize("wide_margin").width

        width: {
            if (newWidth > minWidth) {
                if (newWidth > maxWidth) {
                    return maxWidth
                }
                return newWidth
            }
            return minWidth
        }

        height: {
            if (introScreen.height + productLink.height > minHeight) {
                return introScreen.height + productLink.height
            }
            return minHeight
        }

        anchors.centerIn: parent

        Rectangle {
            id: welcomeRectangle

            color: "#2471ac"
            anchors.fill: parent

            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")

            Item {
                id: introScreen

                visible: proxy.introScreenVisible

                width: welcomeRectangle.width
                height: childrenRect.height


                Label {
                    id: introHeader

                    anchors.horizontalCenter: parent.horizontalCenter
                    width: welcomeRectangle.width

                    topPadding: 2 * UM.Theme.getSize("thick_margin").height

                    horizontalAlignment: Text.AlignHCenter

                    font.pointSize: 25
                    font.bold: true
                    font.family: "Noto Sans"
                    color: "white"

                    text: "Welcome to SmartSlice, " + smartSliceMain.api.firstName
                }

                Image {
                    id: introImage

                    anchors {
                        horizontalCenter: parent.horizontalCenter
                        top: introHeader.bottom
                    }
                    width: 0.25 * welcomeRectangle.width
                    fillMode: Image.PreserveAspectFit
                    source: "../images/smartslice_symbol.png"
                    mipmap: true
                }

                Label {
                    id: introMission

                    anchors {
                        horizontalCenter: parent.horizontalCenter
                        top: introImage.bottom
                    }
                    width: welcomeRectangle.width

                    horizontalAlignment: Text.AlignHCenter

                    font.pointSize: 17
                    font.bold: true
                    font.family: "Noto Sans"
                    color: "white"

                    text: "Our mission is to help you print better parts, faster."
                }

                Label {
                    id: introAction

                    anchors {
                        horizontalCenter: parent.horizontalCenter
                        top: introMission.bottom
                    }
                    // width: welcomeRectangle.width

                    topPadding: UM.Theme.getSize("thick_margin").height

                    horizontalAlignment: Text.AlignHCenter

                    font.pointSize: 17
                    font.family: "Noto Sans"
                    color: "white"

                    text: "Let’s take a quick tour to show you some of the functionality!"
                }
            }

            Item {
                id: homeScreen

                width: welcomeRectangle.width
                height: welcomeRectangle.height - productLink.height

                visible: proxy.welcomeScreenVisible

                Label {
                    id: homeScreenHeader

                    anchors {
                        top: parent.top
                        horizontalCenter: parent.horizontalCenter
                    }
                    width: welcomeRectangle.width

                    topPadding: 4 * UM.Theme.getSize("thick_margin").height
                    bottomPadding: 6 * UM.Theme.getSize("thick_margin").height

                    horizontalAlignment: Text.AlignHCenter

                    font.pointSize: 17
                    font.bold: true
                    font.family: "Noto Sans"
                    color: "white"

                    text: "Click a video to start learning how to use SmartSlice!"
                }

                Item {
                    id: welcomeVideo

                    anchors {
                        top: homeScreenHeader.bottom
                        left: parent.left
                    }

                    width: parent.width / 3
                    height: childrenRect.height

                    SmartSlice.HoverableGIF {
                        id: welcomeVideoImage
                        anchors {
                            top: parent.top
                            left: parent.left
                            leftMargin: 2 * UM.Theme.getSize("wide_margin").width
                            rightMargin: 2 * UM.Theme.getSize("wide_margin").width
                        }

                        width: parent.width - anchors.leftMargin - anchors.rightMargin

                        source: smartSliceMain.urlHandler.welcomeGif

                        playing: false

                        onEntered: {
                            playing = true;
                            scale = 1.1;
                        }

                        onExited: {
                            scale = 1;
                            playing = false;
                            currentFrame = 0;
                        }

                        onClicked: {
                            Qt.openUrlExternally(smartSliceMain.urlHandler.welcome);
                        }

                        tooltipHeader: catalog.i18nc("@textfp", "Take a Tour")
                        tooltipDescription: catalog.i18nc("@textfp", "Take a tour of SmartSlice to get your bearings, and learn "
                            + "how to navigate the workspace to get the most value.")

                        tooltipTarget.x: 0.5 * width
                        tooltipTarget.y: 0
                        tooltipLocation: proxy.tooltipLocations["top"]
                    }

                    Label {
                        anchors {
                            top: welcomeVideoImage.bottom
                            left: parent.left
                        }

                        width: welcomeVideo.width

                        topPadding: UM.Theme.getSize("thick_margin").height

                        horizontalAlignment: Text.AlignHCenter

                        font: UM.Theme.getFont("large_bold")
                        color: "white"

                        text: "Take a Tour"
                    }

                }

                Item {
                    id: tutorial1Video

                    anchors {
                        top: homeScreenHeader.bottom
                        horizontalCenter: parent.horizontalCenter
                    }

                    width: parent.width / 3
                    height: childrenRect.height

                    SmartSlice.HoverableGIF {
                        id: tutorial1Image
                        anchors {
                            top: parent.top
                            left: parent.left
                            leftMargin: 2 * UM.Theme.getSize("wide_margin").width
                            rightMargin: 2 * UM.Theme.getSize("wide_margin").width
                        }

                        width: parent.width - anchors.leftMargin - anchors.rightMargin

                        source: smartSliceMain.urlHandler.tutorial1Gif

                        playing: false

                        onEntered: {
                            playing = true;
                            scale = 1.1;
                        }

                        onExited: {
                            scale = 1.;
                            playing = false;
                            currentFrame = 0;
                        }

                        onClicked: {
                            Qt.openUrlExternally(smartSliceMain.urlHandler.tutorial1);
                        }

                        tooltipHeader: catalog.i18nc("@textfp", "Tutorial 1")
                        tooltipDescription: catalog.i18nc("@textfp", "Learn how to validate as-printed structural performance and "
                            + "manually change settings to influence as-printed structural behavior.")

                        tooltipTarget.x: 0.5 * width
                        tooltipTarget.y: 0
                        tooltipLocation: proxy.tooltipLocations["top"]
                    }

                    Label {
                        anchors {
                            top: tutorial1Image.bottom
                            left: parent.left
                        }

                        width: tutorial1Video.width

                        topPadding: UM.Theme.getSize("thick_margin").height

                        horizontalAlignment: Text.AlignHCenter

                        font: UM.Theme.getFont("large_bold")
                        color: "white"

                        text: "Tutorial 1"
                    }

                }

                Item {
                    id: tutorial2Video

                    anchors {
                        top: homeScreenHeader.bottom
                        right: parent.right
                    }

                    width: parent.width / 3
                    height: childrenRect.height

                    SmartSlice.HoverableGIF {
                        id: tutorial2Image
                        anchors {
                            top: parent.top
                            left: parent.left
                            leftMargin: 2 * UM.Theme.getSize("wide_margin").width
                            rightMargin: 2 * UM.Theme.getSize("wide_margin").width
                        }

                        width: parent.width - anchors.leftMargin - anchors.rightMargin

                        source: smartSliceMain.urlHandler.tutorial2Gif

                        playing: false

                        onEntered: {
                            scale = 1.1;
                            playing = true;
                        }

                        onExited: {
                            scale = 1.;
                            playing = false;
                            currentFrame = 0;
                        }

                        onClicked: {
                            Qt.openUrlExternally(smartSliceMain.urlHandler.tutorial2);
                        }

                        tooltipHeader: catalog.i18nc("@textfp", "Tutorial 2")
                        tooltipDescription: catalog.i18nc("@textfp", "Learn how to optimize slice settings to minimize print time and "
                            + "material usage, while producing a structurally superior part.")

                        tooltipTarget.x: 0.5 * width
                        tooltipTarget.y: 0
                        tooltipLocation: proxy.tooltipLocations["top"]
                    }

                    Label {
                        anchors {
                            top: tutorial2Image.bottom
                            left: parent.left
                        }

                        width: tutorial2Video.width

                        topPadding: UM.Theme.getSize("thick_margin").height

                        horizontalAlignment: Text.AlignHCenter

                        font: UM.Theme.getFont("large_bold")
                        color: "white"

                        text: "Tutorial 2"
                    }

                }


            }

            Label {
                id: productLink

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    bottom: welcomeRectangle.bottom
                }

                topPadding: 2 * UM.Theme.getSize("thick_margin").height
                bottomPadding: 2 * UM.Theme.getSize("thick_margin").height

                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter

                font: UM.Theme.getFont("large_bold")
                color: productLinkMouseArea.containsMouse ? UM.Theme.getColor("primary_hover") : "white"

                text: "Go to Product"

                MouseArea {
                    id: productLinkMouseArea

                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        proxy.setIntroScreenVisibility(false);
                        proxy.setWelcomeScreenVisibility(false);
                    }
                }
            }

            Cura.ActionButton {
                id: welcomeButton

                anchors {
                    right: welcomeRectangle.right
                    verticalCenter: productLink.verticalCenter
                    rightMargin: UM.Theme.getSize("wide_margin").width
                }

                cornerRadius: 4
                color: "white"
                textFont: UM.Theme.getFont("large_bold")
                textColor: "#2471ac"
                outlineColor: "darkblue"
                textHoverColor: "white"

                text: {
                    if (introScreen.visible) {
                        return "Next"
                    } else {
                        return "Dismiss"
                    }
                }

                onClicked: {
                    if (introScreen.visible) {
                        proxy.setIntroScreenVisibility(false);
                        proxy.setWelcomeScreenVisibility(true);
                    } else {
                        proxy.setIntroScreenVisibility(false);
                        proxy.setWelcomeScreenVisibility(false);
                    }
                }
            }
        }
    }
}
import QtQuick 2.10
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.4
import QtGraphicalEffects 1.0

import Cura 1.0 as Cura
import UM 1.2 as UM

import SmartSlice 1.0 as SmartSlice

MouseArea {
    id: loginDialog

    property var authConfig: UM.Controller.activeStage.authConfig

    visible: true

    width: smartSliceMain.width
    height: smartSliceMain.height

    acceptedButtons: Qt.AllButtons
    hoverEnabled: true
    preventStealing: true
    scrollGestureEnabled: false

    onClicked: {}
    onWheel: {}

    Keys.onEnterPressed: {
        if (username_input.acceptableInput && password_input.acceptableInput) {
            smartSliceMain.api.onLoginButtonClicked()
        }
    }

    Keys.onReturnPressed: {
        if (username_input.acceptableInput && password_input.acceptableInput) {
            smartSliceMain.api.onLoginButtonClicked()
        }
    }

    Item {
        id: loginItem

        property int minimumWidth: 350
        property int computedWidth: 0.2 * smartSliceMain.width

        width: computedWidth >= minimumWidth ? computedWidth : minimumWidth
        height: childrenRect.height

        x: (0.5 * smartSliceMain.width) - (loginContainer.width * 0.5)
        y: (0.5 * smartSliceMain.height) - (loginContainer.height * 0.5)

        states: [
            State {
                name: "notLoggedIn"
                when: smartSliceMain.api.authState == "NotLoggedIn"

                PropertyChanges {
                    target: loginDialog
                    visible: true
                }

                PropertyChanges {
                    target: statusText
                    text: ""
                }
            },

            State {
                name: "invalidCredentials"
                when: smartSliceMain.api.authState == "InvalidCredentials"

                PropertyChanges {
                    target: loginDialog
                    visible: true
                }

                PropertyChanges {
                    target: statusText
                    text: "Invalid email or password"
                }
            },

            State {
                name: "oauthError"
                when: smartSliceMain.api.authState == "OAuthError"

                PropertyChanges {
                    target: loginDialog
                    visible: true
                }

                PropertyChanges {
                    target: statusText
                    text: smartSliceMain.api.authError
                }
            },

            State {
                name: "loggedIn"
                when: smartSliceMain.api.authState == "LoggedIn"

                PropertyChanges {
                    target: loginDialog
                    visible: false
                }

                PropertyChanges {
                    target: password_input
                    text: ""
                }

                PropertyChanges {
                    target: statusText
                    text: ""
                }
            }
        ]

        Rectangle {
            id: loginContainer

            color: UM.Theme.getColor("main_background")
            height: childrenRect.height + 4 * UM.Theme.getSize("thick_margin").height
            width: parent.width
            radius: 2
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height

            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")

            Image {
                id: logoImage
                anchors {
                    horizontalCenter: parent.horizontalCenter
                    top: parent.top
                    topMargin: 2 * UM.Theme.getSize("thick_margin").height
                }
                width: loginContainer.width - 2 * UM.Theme.getSize("default_margin").width
                fillMode: Image.PreserveAspectFit
                source: "../images/smartslice_logo.png"
                mipmap: true
            }

            Item {
                id: oauthButtonContainer
                visible: !loginDialog.authConfig.basicAuthEnabled

                height: visible ? childrenRect.height + 2 * UM.Theme.getSize("default_margin").height : 0
                width: parent.width

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    top: logoImage.bottom
                }

                Cura.PrimaryButton {
                    id: oauthButton

                    anchors {
                        top: parent.top
                        topMargin: UM.Theme.getSize("default_margin").height
                        horizontalCenter: parent.horizontalCenter
                    }

                    height: UM.Theme.getSize("action_button").height
                    width: loginContainer.width * 0.4
                    fixedWidthMode: true

                    text: catalog.i18nc("@action:button", "Sign in")

                    onClicked: {
                        loginDialog.authConfig.loginOAuth(false);
                    }
                }

                Text {
                    id: noAccountText

                    anchors {
                        top: oauthButton.bottom
                        topMargin: UM.Theme.getSize("default_margin").height
                        horizontalCenter: parent.horizontalCenter
                    }

                    font: UM.Theme.getFont("medium_bold")

                    color: "#266faa"
                    text: "Don't have an account?"

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            loginDialog.authConfig.loginOAuth(true);
                        }
                    }
                }
            }

            Item {
                id: oauthDirectProviders
                visible: !loginDialog.authConfig.basicAuthEnabled && loginDialog.authConfig.hasDirectIdentityProviders

                height: visible ? childrenRect.height : 0
                width: parent.width

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    top: oauthButtonContainer.bottom
                }

                Column {
                    id: singleSignOnButtonsColumn
                    height: childrenRect.height
                    width: parent.width

                    Repeater {
                        model: loginDialog.authConfig.directIdentityProviders

                        delegate: MouseArea {
                            height: singleSignOnButton.height
                            width: singleSignOnButton.width

                            hoverEnabled: true

                            onEntered: {
                                dropShadow.visible = true;
                            }

                            onExited: {
                                dropShadow.visible = false;
                            }

                            onClicked: {
                                loginDialog.authConfig.login(model.name);
                            }

                            anchors {
                                horizontalCenter: parent.horizontalCenter
                                top: logoImage.bottom
                            }

                            Image {
                                id: singleSignOnButton

                                anchors {
                                    horizontalCenter: parent.horizontalCenter
                                }

                                source: model.buttonImage
                            }

                            DropShadow {
                                id: dropShadow
                                visible: false
                                anchors.fill: singleSignOnButton
                                source: singleSignOnButton
                                horizontalOffset: 3
                                verticalOffset: 3
                                color: UM.Theme.getColor("primary_button_shadow")
                            }
                        }
                    }
                }
            }

            Item {
                id: statusContainer

                height: visible ? childrenRect.height : 0
                width: parent.width

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    top: oauthDirectProviders.bottom
                }

                Text {
                    id: statusText

                    anchors {
                        horizontalCenter: parent.horizontalCenter
                        top: parent.top
                    }

                    height: UM.Theme.getSize("thick_margin").height

                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering
                    color: "red"

                    text: ""
                    visible: true
                }
            }

            Item {
                id: basicAuth
                visible: loginDialog.authConfig.basicAuthEnabled

                height: visible ? childrenRect.height : 0
                width: parent.width

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    top: statusContainer.bottom
                }

                TextField {
                    id: username_input

                    width: parent.width * 0.62
                    anchors {
                        top: parent.top
                        horizontalCenter: parent.horizontalCenter
                        topMargin: UM.Theme.getSize("default_margin").height
                    }

                    validator: RegExpValidator { regExp: /^([a-zA-Z0-9_\-\.\+]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$/ }

                    background: Rectangle {
                        anchors.fill: parent

                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: username_input.hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
                        radius: UM.Theme.getSize("setting_control_radius").width

                        color: UM.Theme.getColor("setting_validation_ok")

                    }

                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")

                    text: smartSliceMain.api.loginUsername

                    onTextChanged: {
                        smartSliceMain.api.loginUsername = text
                    }

                    onAccepted: password_input.forceActiveFocus()
                    placeholderText: catalog.i18nc("@label", "email")
                    KeyNavigation.tab: password_input
                }

                TextField {
                    id: password_input

                    width: parent.width * 0.62
                    anchors {
                        top: username_input.bottom
                        horizontalCenter: parent.horizontalCenter
                        topMargin: UM.Theme.getSize("default_margin").height
                    }

                    validator: RegExpValidator { regExp: /.+/ }

                    background: Rectangle {
                        anchors.fill: parent

                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: password_input.hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
                        radius: UM.Theme.getSize("setting_control_radius").width

                        color: UM.Theme.getColor("setting_validation_ok")

                    }

                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")

                    text: smartSliceMain.api.loginPassword

                    onTextChanged: {
                        smartSliceMain.api.loginPassword = text;
                    }

                    placeholderText: catalog.i18nc("@label", "password")
                    echoMode: TextInput.Password
                    KeyNavigation.tab: login_button
                }

                Text {
                    id: forgotPasswordText

                    anchors {
                        top: password_input.bottom
                        topMargin: UM.Theme.getSize("thick_margin").height
                        horizontalCenter: parent.horizontalCenter
                    }

                    font: UM.Theme.getFont("default")

                    color: "#266faa"
                    text: "Forgot password?"

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Qt.openUrlExternally(smartSliceMain.urlHandler.forgotPassword)
                    }
                }

                Text {
                    id: noAccountTextBasic

                    anchors {
                        top: forgotPasswordText.bottom
                        topMargin: UM.Theme.getSize("default_margin").height
                        horizontalCenter: parent.horizontalCenter
                    }

                    font: UM.Theme.getFont("medium_bold")

                    color: "#266faa"
                    text: "Don't have an account?"

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Qt.openUrlExternally(smartSliceMain.urlHandler.trailRegistration)
                    }
                }

                Cura.PrimaryButton {
                    id: login_button

                    anchors {
                        top: noAccountTextBasic.bottom
                        topMargin: 2 * UM.Theme.getSize("default_margin").height
                        bottomMargin: UM.Theme.getSize("default_margin").height
                        horizontalCenter: parent.horizontalCenter
                    }

                    height: UM.Theme.getSize("action_button").height
                    width: loginContainer.width * 0.4
                    fixedWidthMode: true

                    enabled: username_input.acceptableInput && password_input.acceptableInput

                    text: catalog.i18nc("@action:button", "Sign in")
                    textDisabledColor: textColor

                    onClicked: {
                        smartSliceMain.api.onLoginButtonClicked()
                    }

                    KeyNavigation.tab: username_input
                }


            }
        }
    }
}
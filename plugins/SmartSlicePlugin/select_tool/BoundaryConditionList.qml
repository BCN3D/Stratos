import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.4

import UM 1.4 as UM
import Cura 1.1 as Cura

import SmartSlice 1.0 as SmartSlice

Column {
    id: mainColumn

    property int maximumHeight: 6 * UM.Theme.getSize("section_icon").width
    property string addButtonText: "Add"
    property int boundaryConditionType: 0
    property SmartSlice.BoundaryConditionListModel model: bcListModel

    signal selectionChanged(int index)

    width: constraintsTooltip.width
    height: childrenRect.height

    anchors.topMargin: UM.Theme.getSize("default_margin").width

    spacing: UM.Theme.getSize("default_margin").height

    onVisibleChanged: {
        if (visible) {
            bcListModel.activate(bcListView.currentIndex);

        } else {
            bcListModel.deactivate();
        }
    }

    ScrollView {

        id: bcScroll

        height: bcListItem.height > mainColumn.maximumHeight ? mainColumn.maximumHeight : bcListItem.height

        width: parent.width
        style: UM.Theme.styles.scrollview

        verticalScrollBarPolicy: Qt.ScrollBarAsNeeded
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        clip: true

        Item {
            id: bcListItem

            height: bcListView.height
            width: parent.width

            ListView {
                id: bcListView

                property var itemHeight: UM.Theme.getFont("default").pixelSize + 2 * UM.Theme.getSize("thin_margin").height

                spacing: UM.Theme.getSize("default_lining").height

                height: itemHeight * bcListView.count

                model: SmartSlice.BoundaryConditionListModel {
                    id: bcListModel
                    boundaryConditionType: mainColumn.boundaryConditionType
                }

                Component.onCompleted: {
                    bcListView.height = itemHeight * count
                    mainColumn.forceLayout()
                }

                onCountChanged: {
                    height = itemHeight * bcListView.count
                }

                onCurrentItemChanged: {
                    if (mainColumn.visible) {
                        bcListModel.select(currentIndex);
                        mainColumn.selectionChanged(currentIndex);
                    }
                }

                delegate: Rectangle {
                    width: mainColumn.width - 2 * UM.Theme.getSize("thin_margin").width
                    height: bcListView.itemHeight

                    color: UM.Theme.getColor("main_background")

                    Rectangle {
                        width: parent.width - 1.5 * Math.round(UM.Theme.getSize("setting").height / 2)
                        height: parent.height
                        anchors {
                            left: parent.left
                            topMargin: UM.Theme.getSize("thin_margin").height
                            bottomMargin: UM.Theme.getSize("thin_margin").height
                        }
                        border.width: bcListView.currentIndex == index ? 2 : 0
                        border.color: UM.Theme.getColor("action_button_active_border")
                        color: UM.Theme.getColor("main_background")

                        Text {
                            width: parent.width - UM.Theme.getSize("thin_margin").width
                            anchors {
                                left: parent.left
                                leftMargin: UM.Theme.getSize("default_margin").width
                                verticalCenter: parent.verticalCenter
                            }

                            verticalAlignment: TextInput.AlignVCenter
                            font: UM.Theme.getFont("default")
                            renderType: Text.NativeRendering

                            text: model.name
                            color: bcListView.currentIndex == index ?
                                UM.Theme.getColor("secondary_button_text") : UM.Theme.getColor("text")

                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    bcListModel.select(index)
                                    bcListView.currentIndex = index
                                    mainColumn.selectionChanged(index)
                                }
                            }
                        }
                    }
                    Button {
                        width: Math.round(UM.Theme.getSize("setting").height / 2)
                        height: UM.Theme.getSize("setting").height
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        visible : bcListView.count > 1 ? true: false

                        onClicked: {
                            bcListModel.remove(index)
                            mainColumn.selectionChanged(bcListView.currentIndex)
                            mainColumn.forceLayout()
                        }
                        style: ButtonStyle {
                            background: Item {
                                UM.RecolorImage {
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width
                                    height: width
                                    sourceSize.height: width
                                    color: control.hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button")
                                    source: UM.Theme.getIcon("minus")
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Cura.SecondaryButton {
        id: addButton
        shadowEnabled: false

        text: catalog.i18nc("@action:button", mainColumn.addButtonText);

        onClicked: {
            bcListModel.add()
            bcListView.currentIndex = bcListView.count - 1
            bcListModel.select(bcListView.currentIndex)
            mainColumn.selectionChanged(bcListView.currentIndex)
            mainColumn.forceLayout()
        }
    }
}

import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Templates as T
import QtQuick.Controls 2.15

Slider {
    from: 1
    to: 9
    value: 5
    implicitWidth: 300
    implicitHeight: 50
    width: implicitWidth
    height: implicitHeight
    snapMode: Slider.SnapOnRelease
    background: Item {
        x: leftPadding + 13
        y: topPadding + availableHeight / 2
        width: availableWidth - 26
        Repeater {
            model: (to - from) / stepSize + 1
            delegate: Column {
                x: index * parent.width / (to - from) * stepSize - width / 2
                y: 0
                spacing: 2
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 1
                    height: 10
                    color: "grey"
                }
            }
        }
        Rectangle {
            y: -height / 20
            width: parent.width
            height: 6
            color: "#767676"
            Rectangle {
                width: visualPosition * parent.width
                height: parent.height
                color: "#196EF0"
            }
        }
    }
    handle: Rectangle {
        x: leftPadding + visualPosition * (availableWidth - width)
        y: topPadding + 3 + availableHeight  / 2 - height / 2
        implicitWidth: 20
        implicitHeight: 20
        radius: 30
        color: pressed ? "#f0f0f0" : "#f6f6f6"
        border.color: "#bdbebf"
        Rectangle {
            x: parent.width / 2 - 2
            y: parent.height / 2 - height / 2
            width: 1
            height: parent.height / 3
            color: "#ccc"
        }
        Rectangle {
            x: parent.width / 2 + 1
            y: parent.height / 2 - height / 2
            width: 1
            height: parent.height / 3
            color: "#ccc"
        }
    }
}
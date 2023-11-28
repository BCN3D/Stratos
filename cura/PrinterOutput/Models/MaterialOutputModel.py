# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt6.QtCore import pyqtProperty, QObject


class MaterialOutputModel(QObject):
    def __init__(self, guid: Optional[str], type: str, color: str, brand: str, name: str, parent = None) -> None:
        super().__init__(parent)
        self._guid = guid
        self._type = type
        self._color = color
        self._brand = brand
        self._name = name

    @pyqtProperty(str, constant = True)
    def guid(self) -> str:
        return self._guid if self._guid else ""

    @pyqtProperty(str, constant = True)
    def type(self) -> str:
        return self._type

    @pyqtProperty(str, constant = True)
    def brand(self) -> str:
        return self._brand

    @pyqtProperty(str, constant = True)
    def color(self) -> str:
        return self._color

    @pyqtProperty(str, constant = True)
    def name(self) -> str:
        return self._name

    def __eq__(self, other):
        if self is other:
            return True
        if type(other) is not MaterialOutputModel:
            return False

        return self.guid == other.guid and self.type == other.type and self.brand == other.brand and self.color == other.color and self.name == other.name

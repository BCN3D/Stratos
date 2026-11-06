import base64

from UM.Extension import Extension
from PyQt6.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QObject
from PyQt6.QtCore import QBuffer
from UM.Application import Application
from cura.CuraApplication import CuraApplication
from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
from cura.Snapshot import Snapshot

from .Bcn3DFixes import Bcn3DFixes

catalog = i18nCatalog("cura")

class BCN3DPostSlicing(QObject, Extension):
    THUMBNAIL_WIDTH = 300
    THUMBNAIL_HEIGHT = 300
    THUMBNAIL_CHUNK_SIZE = 78

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        Extension.__init__(self)
        self._bcn3d_fixes_job = None
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self.applyPostSlice)
        self._application = CuraApplication.getInstance()
        #self._application.getOutputDeviceManager().writeStarted.writeStarted.connect(self.applyPostSlice)

    def applyPostSlice(self, output_device)  -> None:
        if self._bcn3d_fixes_job is not None and self._bcn3d_fixes_job.isRunning():
            return
        container = Application.getInstance().getGlobalContainerStack()
        scene = Application.getInstance().getController().getScene()
        if hasattr(scene, "gcode_dict"):
            gcode_dict = getattr(scene, "gcode_dict")
            if gcode_dict:
                #self._addThumbnails(gcode_dict)
                for i in gcode_dict:
                    self._bcn3d_fixes_job = Bcn3DFixes(container, gcode_dict[i])
                    self._bcn3d_fixes_job.start()

    def _addThumbnails(self, gcode_dict) -> None:
        """Embed a scene thumbnail in every build plate that does not have one yet."""
        gcode_lists_without_thumbnail = [
            gcode_list for gcode_list in gcode_dict.values()
            if gcode_list and not self._hasThumbnail(gcode_list)
        ]
        if not gcode_lists_without_thumbnail:
            return

        try:
            # IDEX copies are visual-only nodes, so include them in the thumbnail
            # without making them sliceable or adding them to the G-code.
            snapshot = Snapshot.snapshot(
                self.THUMBNAIL_WIDTH,
                self.THUMBNAIL_HEIGHT,
                include_duplicated_nodes = True,
                add_print_mode_indicator = True
            )
            if snapshot is None:
                Logger.log("w", "Unable to create the G-code thumbnail: the build plate is empty")
                return

            thumbnail_gcode = self._thumbnailGcode(snapshot)
        except Exception:
            Logger.logException("w", "Unable to create the G-code thumbnail")
            return

        for gcode_list in gcode_lists_without_thumbnail:
            self._insertThumbnail(gcode_list, thumbnail_gcode)

    @staticmethod
    def _hasThumbnail(gcode_list) -> bool:
        return any("; thumbnail begin " in gcode_layer for gcode_layer in gcode_list)

    def _thumbnailGcode(self, snapshot):
        thumbnail_buffer = QBuffer()
        thumbnail_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        try:
            if not snapshot.save(thumbnail_buffer, "PNG"):
                raise RuntimeError("Could not encode the thumbnail as PNG")
            encoded_snapshot = base64.b64encode(bytes(thumbnail_buffer.data())).decode("ascii")
        finally:
            thumbnail_buffer.close()

        thumbnail_gcode = [
            ";",
            "; thumbnail begin {}x{} {}".format(
                self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT, len(encoded_snapshot)
            )
        ]
        thumbnail_gcode.extend(
            "; " + encoded_snapshot[index:index + self.THUMBNAIL_CHUNK_SIZE]
            for index in range(0, len(encoded_snapshot), self.THUMBNAIL_CHUNK_SIZE)
        )
        thumbnail_gcode.extend(["; thumbnail end", ";", ""])
        return thumbnail_gcode

    @staticmethod
    def _insertThumbnail(gcode_list, thumbnail_gcode) -> None:
        """Insert the thumbnail after the start-up sequence of a G-code file.

        BCN3D start G-code writes the selected print mode before heating and
        machine initialization.  The thumbnail must come after that sequence,
        not between the G-code header and the temperature commands.
        """
        generated_prefixes = (";Generated with Cura", ";Generated with StratosEngine")
        print_mode_found = False

        for index, gcode_layer in enumerate(gcode_list):
            lines = gcode_layer.split("\n")
            for line_index, line in enumerate(lines):
                if line.startswith(";Print mode:"):
                    print_mode_found = True
                elif print_mode_found and line.lstrip().startswith("M107"):
                    lines[line_index + 1:line_index + 1] = thumbnail_gcode
                    gcode_list[index] = "\n".join(lines)
                    return

        for index, gcode_layer in enumerate(gcode_list):
            lines = gcode_layer.split("\n")
            for line_index, line in enumerate(lines):
                if line.startswith(generated_prefixes):
                    lines[line_index + 1:line_index + 1] = thumbnail_gcode
                    gcode_list[index] = "\n".join(lines)
                    Logger.log("w", "G-code start-up sequence not found; added thumbnail after generator header")
                    return

        Logger.log("w", "Unable to add the G-code thumbnail: generator header not found")

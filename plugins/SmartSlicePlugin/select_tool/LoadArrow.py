from UM.Math.Vector import Vector
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.ToolHandle import ToolHandle

from .LoadToolHandle import LoadToolHandle

class LoadArrow(LoadToolHandle):
    """Provides the arrow for the load direction"""

    def __init__(self, parent = None):
        super().__init__(parent, name="LoadArrow")

        self.direction = -Vector.Unit_X

    def buildMesh(self, pull: bool = False):
        """Builds the mesh based on a push/pull - which sets if the head or tail is built first"""

        super().buildMesh()

        start = Vector(0, 0, 0)

        if pull:
            self.direction = -self.direction
        else:
            start -= LoadToolHandle.ARROW_TOTAL_LENGTH * self.direction

        mb = self._arrow(
            start,
            LoadToolHandle.ARROW_TAIL_WIDTH,
            LoadToolHandle.ARROW_TAIL_LENGTH,
            LoadToolHandle.ARROW_HEAD_WIDTH,
            self._y_axis_color
        )
        self.setSolidMesh(mb.build())

        mb = self._arrow(
            start,
            LoadToolHandle.ACTIVE_ARROW_TAIL_WIDTH,
            LoadToolHandle.ACTIVE_ARROW_TAIL_LENGTH,
            LoadToolHandle.ACTIVE_ARROW_HEAD_WIDTH,
            ToolHandle.YAxisSelectionColor
        )
        self.setSelectionMesh(mb.build())

    @property
    def headPosition(self):
        return self.getPosition()

    @property
    def tailPosition(self):
        return self.getPosition() - self.direction * self.ARROW_TOTAL_LENGTH

    def _arrow(self, start: Vector, tail_width, tail_length, head_width, color) -> MeshBuilder:

        mb = MeshBuilder()

        p_head = Vector(
            start.x + self.direction.x * LoadToolHandle.ARROW_TOTAL_LENGTH,
            start.y + self.direction.y * LoadToolHandle.ARROW_TOTAL_LENGTH,
            start.z + self.direction.z * LoadToolHandle.ARROW_TOTAL_LENGTH
        )

        p_base0 = Vector(
            start.x + self.direction.x * tail_length,
            start.y + self.direction.y * tail_length,
            start.z + self.direction.z * tail_length
        )

        p_tail0 = start

        p_base1 = Vector(p_base0.x, p_base0.y + head_width, p_base0.z)
        p_base2 = Vector(p_base0.x, p_base0.y - head_width, p_base0.z)
        p_base3 = Vector(p_base0.x + head_width, p_base0.y, p_base0.z)
        p_base4 = Vector(p_base0.x - head_width, p_base0.y, p_base0.z)
        p_base5 = Vector(p_base0.x, p_base0.y, p_base0.z + head_width)
        p_base6 = Vector(p_base0.x, p_base0.y, p_base0.z - head_width)

        mb.addFace(p_base1, p_head, p_base3, color=color)
        mb.addFace(p_base3, p_head, p_base2, color=color)
        mb.addFace(p_base2, p_head, p_base4, color=color)
        mb.addFace(p_base4, p_head, p_base1, color=color)
        mb.addFace(p_base5, p_head, p_base1, color=color)
        mb.addFace(p_base6, p_head, p_base1, color=color)
        mb.addFace(p_base6, p_head, p_base2, color=color)
        mb.addFace(p_base2, p_head, p_base5, color=color)
        mb.addFace(p_base3, p_head, p_base5, color=color)
        mb.addFace(p_base5, p_head, p_base4, color=color)
        mb.addFace(p_base4, p_head, p_base6, color=color)
        mb.addFace(p_base6, p_head, p_base3, color=color)

        p_tail1 = Vector(p_tail0.x, p_tail0.y + tail_width, p_tail0.z)
        p_tail2 = Vector(p_tail0.x, p_tail0.y - tail_width, p_tail0.z)
        p_tail3 = Vector(p_tail0.x + tail_width, p_tail0.y, p_tail0.z)
        p_tail4 = Vector(p_tail0.x - tail_width, p_tail0.y, p_tail0.z)
        p_tail5 = Vector(p_tail0.x, p_tail0.y, p_tail0.z + tail_width)
        p_tail6 = Vector(p_tail0.x, p_tail0.y, p_tail0.z - tail_width)

        p_tail_base1 = Vector(p_base0.x, p_base0.y + tail_width, p_base0.z)
        p_tail_base2 = Vector(p_base0.x, p_base0.y - tail_width, p_base0.z)
        p_tail_base3 = Vector(p_base0.x + tail_width, p_base0.y, p_base0.z)
        p_tail_base4 = Vector(p_base0.x - tail_width, p_base0.y, p_base0.z)
        p_tail_base5 = Vector(p_base0.x, p_base0.y, p_base0.z + tail_width)
        p_tail_base6 = Vector(p_base0.x, p_base0.y, p_base0.z - tail_width)

        mb.addFace(p_tail1, p_tail_base1, p_tail3, color=color)
        mb.addFace(p_tail3, p_tail_base3, p_tail2, color=color)
        mb.addFace(p_tail2, p_tail_base2, p_tail4, color=color)
        mb.addFace(p_tail4, p_tail_base4, p_tail1, color=color)
        mb.addFace(p_tail5, p_tail_base5, p_tail1, color=color)
        mb.addFace(p_tail6, p_tail_base6, p_tail1, color=color)
        mb.addFace(p_tail6, p_tail_base6, p_tail2, color=color)
        mb.addFace(p_tail2, p_tail_base2, p_tail5, color=color)
        mb.addFace(p_tail3, p_tail_base3, p_tail5, color=color)
        mb.addFace(p_tail5, p_tail_base5, p_tail4, color=color)
        mb.addFace(p_tail4, p_tail_base4, p_tail6, color=color)
        mb.addFace(p_tail6, p_tail_base6, p_tail3, color=color)

        mb.addFace(p_tail_base1, p_tail_base3, p_tail3, color=color)
        mb.addFace(p_tail_base3, p_tail_base2, p_tail2, color=color)
        mb.addFace(p_tail_base2, p_tail_base4, p_tail4, color=color)
        mb.addFace(p_tail_base4, p_tail_base1, p_tail1, color=color)
        mb.addFace(p_tail_base5, p_tail_base1, p_tail1, color=color)
        mb.addFace(p_tail_base6, p_tail_base1, p_tail1, color=color)
        mb.addFace(p_tail_base6, p_tail_base2, p_tail2, color=color)
        mb.addFace(p_tail_base2, p_tail_base5, p_tail5, color=color)
        mb.addFace(p_tail_base3, p_tail_base5, p_tail5, color=color)
        mb.addFace(p_tail_base5, p_tail_base4, p_tail4, color=color)
        mb.addFace(p_tail_base4, p_tail_base6, p_tail6, color=color)
        mb.addFace(p_tail_base6, p_tail_base3, p_tail3, color=color)

        return mb

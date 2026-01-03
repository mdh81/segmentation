from dataclasses import dataclass
from typing import List, Optional

import math3d
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray

from segmentation.style import Styles


@dataclass(slots=True, frozen=True)
class Triangle:
    i: int
    j: int
    k: int


class TriangleMesh:

    def __init__(self, category: str):
        self._vertices: List[math3d.vector3] = []
        self._triangles: List[Triangle] = []
        self._transform: Optional[math3d.matrix4] = None
        self._polydata: Optional[vtkPolyData] = None
        self._styles: Optional[Styles] = None
        self._type = category

    def __str__(self):
        s = f'Triangle Mesh of type: {self._type}\n'
        s += f'\tNumber of vertices: {len(self._vertices)}\n'
        s += f'\tNumber of triangles: {len(self._triangles)}\n'
        s += f'\tTransform:\n{self._transform}\n'
        s += f'\tRenderer Styles: {self._styles}\n'
        return s

    @property
    def category(self) -> str:
        return self._type

    @property
    def vertices(self) -> List[math3d.vector3]:
        return self._vertices

    @vertices.setter
    def vertices(self, points: List[float]):
        for i in range(0, len(points), 3):
            self._vertices.append(math3d.vector3(points[i], points[i + 1], points[i + 2]))

    @property
    def triangles(self) -> List[Triangle]:
        return self._triangles

    @triangles.setter
    def triangles(self, tris: List[int]):
        for i in range(0, len(tris), 3):
            self._triangles.append(Triangle(tris[i], tris[i + 1], tris[i + 2]))

    @property
    def transform(self) -> Optional[math3d.matrix4]:
        return self._transform

    @transform.setter
    def transform(self, matrix):
        self._transform = \
            math3d.matrix4([matrix[i:i + 4] for i in range(0, len(matrix), 4)], math3d.col_major)

    @property
    def polydata(self) -> Optional[vtkPolyData]:
        if not self._polydata:
            self._polydata = self._build_polydata()
        return self._polydata

    @property
    def styles(self) -> Optional[Styles]:
        return self._styles

    @styles.setter
    def styles(self, styles: Styles):
        self._styles = styles

    def _build_polydata(self) -> Optional[vtkPolyData]:
        if not self._vertices or not self._triangles:
            return None

        points = vtkPoints()
        points.SetNumberOfPoints(len(self._vertices))
        for i in range(0, len(self._vertices)):
            point = self._transform * math3d.vector4(self._vertices[i])
            points.SetPoint(i, point.x, point.y, point.z)

        cell_array = vtkCellArray()
        cell_array.AllocateEstimate(len(self._triangles), 3)
        for tri in self._triangles:
            cell_array.InsertNextCell(3)
            cell_array.InsertCellPoint(tri.i)
            cell_array.InsertCellPoint(tri.j)
            cell_array.InsertCellPoint(tri.k)

        poly_data = vtkPolyData()
        poly_data.SetPoints(points)
        poly_data.SetPolys(cell_array)

        return poly_data

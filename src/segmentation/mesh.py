# Copyright (c) 2025 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from dataclasses import dataclass
from typing import List, Optional, Tuple

import math3d
from vtkmodules.vtkCommonCore import vtkPoints, vtkLookupTable, vtkIntArray
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray
from vtkmodules.vtkRenderingCore import vtkProperty

from segmentation.style import Styles


@dataclass(slots=True, frozen=True)
class Triangle:
    i: int
    j: int
    k: int


class TriangleMesh:
    """
    A triangle mesh that can be built from a list of vec3s and i,j,k tuples that define
    connectivity into the former vec3 list. Converts this mesh to a polydata that can be
    rendered by a vtk renderer. Aggregates styles and manages them via a lookup table or
    a single property if there is a 1:1 relationship between itself and a style
    """

    def __init__(self, category: str):
        self._vertices: List[math3d.Vector3] = []
        self._triangles: List[Triangle] = []
        self._transform: Optional[math3d.Matrix4] = None
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
    def vertices(self) -> List[math3d.Vector3]:
        return self._vertices

    @vertices.setter
    def vertices(self, points: List[float]):
        for i in range(0, len(points), 3):
            self._vertices.append(math3d.Vector3(points[i], points[i + 1], points[i + 2]))

    @property
    def triangles(self) -> List[Triangle]:
        return self._triangles

    @triangles.setter
    def triangles(self, tris: List[int]):
        for i in range(0, len(tris), 3):
            self._triangles.append(Triangle(tris[i], tris[i + 1], tris[i + 2]))

    @property
    def transform(self) -> Optional[math3d.Matrix4]:
        return self._transform

    @transform.setter
    def transform(self, matrix):
        self._transform = \
            math3d.Matrix4([matrix[i:i + 4] for i in range(0, len(matrix), 4)], math3d.col_major)

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

    def get_lut_and_prop(self) -> Tuple[vtkLookupTable | None, vtkProperty]:
        # NOTE
        # 1. Set the prop opacity to 1 so the opacity from lut is used
        # 2. Use the first style's specular when there are multiple styles involved to keep this app simple
        styles = self.styles.list
        num_styles = len(styles)
        prop: vtkProperty = styles[0].style
        if num_styles > 1:
            lut = vtkLookupTable()
            lut.SetNumberOfTableValues(num_styles)
            for i in range(0, num_styles):
                lut.SetTableValue(i, styles[i].diffuse.r, styles[i].diffuse.g, styles[i].diffuse.b, styles[i].alpha)
            prop.SetOpacity(1)
            return lut, prop
        else:
            return None, prop

    def _build_polydata(self) -> Optional[vtkPolyData]:
        if not self._vertices or not self._triangles:
            return None

        points = vtkPoints()
        points.SetNumberOfPoints(len(self._vertices))
        for i in range(0, len(self._vertices)):
            point = self._transform * math3d.Vector4(self._vertices[i])
            points.SetPoint(i, point.x, point.y, point.z)

        cell_array = vtkCellArray()
        cell_array.AllocateEstimate(len(self._triangles), 3)
        for tri in self._triangles:
            cell_array.InsertNextCell(3)
            cell_array.InsertCellPoint(tri.i)
            cell_array.InsertCellPoint(tri.j)
            cell_array.InsertCellPoint(tri.k)

        style_cell_ids = vtkIntArray()
        style_cell_ids.SetName('Style Id')
        style_cell_ids.SetNumberOfComponents(1)
        style_cell_ids.SetNumberOfTuples(len(self._triangles))

        styles = self._styles.list
        for i in range(0, len(styles)):
            face_ids = self._styles.get_faces(styles[i])
            for face_id_range in face_ids:
                for face_id in range(face_id_range[0], face_id_range[1] + 1):
                    style_cell_ids.SetTuple1(face_id, i)

        poly_data = vtkPolyData()
        poly_data.SetPoints(points)
        poly_data.SetPolys(cell_array)
        poly_data.GetCellData().SetScalars(style_cell_ids)

        return poly_data

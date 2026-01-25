# Copyright (c) 2026 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import annotations

import argparse
from typing import List, Tuple

from math3d import AABB, Extent, Vector3, Vector4
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray
from vtkmodules.vtkFiltersCore import vtkAppendPolyData
from vtkmodules.vtkFiltersSources import vtkSphereSource, vtkConeSource

from segmentation.mesh import TriangleMesh
from segmentation.reader import E57Reader, IFCReader
from segmentation.renderer import Renderer, MeshRep

_MAX_DEFAULT_OCTREE_LEVELS: int = 3
_NUM_PTS_IN_OCTANT_FACE_LOOP: int = 5


class Octant:
    _MAX_LEVELS: int = _MAX_DEFAULT_OCTREE_LEVELS

    def __init__(self, min_corner: Vector3, max_corner: Vector3, parent: Octant | None = None):
        self._parent = parent
        self._center = (min_corner + max_corner) * 0.5
        self._length = (max_corner.x - min_corner.x, max_corner.y - min_corner.y, max_corner.z - min_corner.z)
        self._level = 1 if parent is None else parent.level + 1
        self._children: List[Octant] = []
        self._bounds: AABB = AABB(Extent(min_corner.x, max_corner.x),
                                  Extent(min_corner.y, max_corner.y),
                                  Extent(min_corner.z, max_corner.z))
        self._subdivide()

    @property
    def length(self) -> Tuple[float, float, float]:
        return self._length

    @property
    def center(self) -> Vector3:
        return self._center

    @property
    def level(self) -> int:
        return self._level

    @property
    def children(self) -> List[Octant]:
        return self._children

    def _subdivide(self):
        if self.level == Octant._MAX_LEVELS:
            self._children = []
            return

        half_lengths = tuple(self.length[i] * 0.5 for i in range(3))
        dir_vectors: List[Vector3] = [Vector3(half_lengths[0] * x, half_lengths[1] * y, half_lengths[2] * z)
                                      for x in (-1, +1)
                                      for y in (-1, +1)
                                      for z in (-1, +1)]
        self._children.clear()
        for dir_vector in dir_vectors:
            corner: Vector3 = self.center + dir_vector
            min_corner: Vector3 = Vector3(min(corner.x, self.center.x), min(corner.y, self.center.y),
                                          min(corner.z, self.center.z))
            max_corner: Vector3 = Vector3(max(corner.x, self.center.x), max(corner.y, self.center.y),
                                          max(corner.z, self.center.z))
            self._children.append(Octant(min_corner, max_corner, self))

    def leaves(self, leaves: List[Octant]):
        if not self._children:
            leaves.append(self)
            return

        for child in self._children:
            child.leaves(leaves)

    @property
    def polydata(self) -> vtkPolyData | None:
        if self.level == Octant._MAX_LEVELS:
            polydata: vtkPolyData = vtkPolyData()
            points: vtkPoints = vtkPoints()
            corners: List[Vector3] = self._bounds.corners
            points.SetNumberOfPoints(len(corners))
            for i in range(len(corners)):
                points.SetPoint(i, corners[i].x, corners[i].y, corners[i].z)
            edges: List[List[int]] = self._bounds.edges
            cells: vtkCellArray = vtkCellArray()
            cells.AllocateEstimate(len(edges), _NUM_PTS_IN_OCTANT_FACE_LOOP)
            for a, b, c, d in edges:
                cells.InsertNextCell(_NUM_PTS_IN_OCTANT_FACE_LOOP, [a, b, c, d, a])
            polydata.SetPoints(points)
            polydata.SetLines(cells)
            return polydata
        return None


class Octree:

    def __init__(self, bounds: AABB = None):
        self._octant: Octant | None = Octant(bounds.min, bounds.max) if bounds else None

    @classmethod
    def from_polydata(cls, polydata: vtkPolyData):
        pd_bounds: Tuple[float, ...] = polydata.GetBounds()
        x: Extent = Extent(pd_bounds[0], pd_bounds[1])
        y: Extent = Extent(pd_bounds[2], pd_bounds[3])
        z: Extent = Extent(pd_bounds[4], pd_bounds[5])
        bounds: AABB = AABB(x, y, z)
        return Octree(bounds)

    def add(self, trimeshes: List[TriangleMesh]):
        bounds: AABB = AABB()
        x: Extent = Extent()
        y: Extent = Extent()
        z: Extent = Extent()
        for trimesh in trimeshes:
            for vertex in trimesh.vertices:
                transformed_vertex = trimesh.transform * Vector4(vertex)
                x.update(transformed_vertex.x)
                y.update(transformed_vertex.y)
                z.update(transformed_vertex.z)
            trimesh_bounds: AABB = AABB(x, y, z)
            bounds.merge(trimesh_bounds)
        self._octant = Octant(bounds.min, bounds.max)

    @property
    def leaves(self) -> List[Octant]:
        leaves: List[Octant] = []
        self._octant.leaves(leaves)
        return leaves

    @property
    def polydata(self):
        leaves: List[Octant] = self.leaves
        append_polydata: vtkAppendPolyData = vtkAppendPolyData()
        for leaf in leaves:
            append_polydata.AddInputData(leaf.polydata)
        append_polydata.Update()
        return append_polydata.GetOutput()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='Octree Test',
    )
    parser.add_argument('-mdl', help='Model to generate octree for in IFC or e57 format')
    parser.add_argument('-vtk', help='Generate octree for a sample vtk polydata', action='store_true')
    args = parser.parse_args()

    renderer: Renderer = Renderer()

    if not args.mdl and not args.vtk:
        octree = Octree(AABB(Vector3(-10, -10, -10), Vector3(10, 10, 10)))
        renderer.others.append(octree.polydata)
    elif args.vtk:
        append = vtkAppendPolyData()
        sphere = vtkSphereSource()
        sphere.SetRadius(3)
        sphere.SetThetaResolution(25)
        sphere.SetPhiResolution(25)
        append.AddInputConnection(0, sphere.GetOutputPort())
        cone = vtkConeSource()
        cone.SetResolution(10)
        cone.SetCenter(10, 10, 10)
        append.AddInputConnection(0, cone.GetOutputPort())
        append.Update()
        octree = Octree.from_polydata(append.GetOutput())
        renderer.others.append(octree.polydata)
        renderer.others.append(append.GetOutput())
    else:
        if args.mdl.endswith('.e57'):
            reader: E57Reader = E57Reader(args.mdl)
            renderer.pointcloud = reader.pointcloud.polydata
            octree = Octree(reader.pointcloud.bounds)
            renderer.others.append(octree.polydata)
        elif args.mdl.endswith('.ifc'):
            reader: IFCReader = IFCReader(args.mdl)
            meshes = reader.meshes
            octree = Octree()
            for mesh in meshes:
                renderer.meshes.append(MeshRep(mesh.polydata, mesh.category, mesh.get_lut_and_prop()))
            octree.add(meshes)
            renderer.others.append(octree.polydata)

    renderer.render()

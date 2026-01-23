# Copyright (c) 2025 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
from dataclasses import dataclass

import vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from typing import Tuple, List

_USE_SAMPLE_DATA: bool = False


@dataclass(slots=True, frozen=True)
class MeshRep:
    polydata: vtk.vtkPolyData
    category: str
    style: Tuple[vtk.vtkLookupTable | None, vtk.vtkProperty]


class Renderer:
    """
        A vtk-based renderer for triangle meshes and point cloud.
        Relies on @:type MeshRep to provide polydata representation
        of triangle meshes along with a lookup table that provides
        cell colors (or a single property if style is uniform across the mesh)
        Relies on @:type PointCloud to provide a point set polydata
        Can optionally render sample geometries and other supporting data like
        octrees if they are converted to vtk polydata and set via property "others"
    """

    @property
    def meshes(self):
        return self._meshes

    @property
    def others(self):
        return self._others

    @property
    def pointcloud(self):
        return self._pointcloud

    @pointcloud.setter
    def pointcloud(self, pointcloud: vtk.vtkPolyData):
        self._pointcloud = pointcloud

    @property
    def filter(self) -> List[str]:
        return self._filter

    def __init__(self, size: Tuple[int, int] = (1024, 768)):
        self._SIZE: Tuple[int, int] = size

        self._ren_win = vtkRenderWindow()
        self._ren_win.SetSize(self._SIZE[0], self._SIZE[1])
        self._iren = vtkRenderWindowInteractor()
        self._iren.SetRenderWindow(self._ren_win)
        self._iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self._renderer = vtkRenderer()
        self._colors = vtkNamedColors()
        self._renderer.SetBackground(self._colors.GetColor3d('AliceBlue'))
        self._renderer.UseDepthPeelingOn()
        self._ren_win.AddRenderer(self._renderer)
        self._meshes: List[MeshRep] = []
        self._filter: List[str] = []
        self._pointcloud: vtk.vtkPolyData | None = None
        self._others: List[vtk.vtkPolyData] = []

    def _add_sample_data(self):
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetThetaResolution(25)
        sphere_source.SetPhiResolution(25)
        sphere_mapper = vtk.vtkPolyDataMapper()
        sphere_mapper.SetInputConnection(sphere_source.GetOutputPort())
        sphere_actor = vtk.vtkActor()
        sphere_actor.SetMapper(sphere_mapper)
        self._renderer.AddActor(sphere_actor)

    def _is_filtered_out(self, mesh: MeshRep) -> bool:
        return self._filter and mesh.category not in self._filter

    def _add_meshes(self):
        for mesh in (mesh for mesh in self.meshes if not self._is_filtered_out(mesh)):
            lut = mesh.style[0]
            prop = mesh.style[1]
            mesh_mapper = vtk.vtkPolyDataMapper()
            mesh_mapper.SetInputData(mesh.polydata)
            if lut:
                mesh_mapper.SetLookupTable(lut)
                mesh_mapper.SetScalarModeToUseCellData()
            else:
                mesh_mapper.ScalarVisibilityOff()
            mesh_actor = vtk.vtkActor()
            mesh_actor.SetProperty(prop)
            mesh_actor.SetMapper(mesh_mapper)
            self._renderer.AddActor(mesh_actor)

    def _add_pointcloud(self):
        if self._pointcloud:
            pointcloud_mapper = vtk.vtkPolyDataMapper()
            pointcloud_mapper.SetInputData(self._pointcloud)
            if self._pointcloud.GetPointData().GetNumberOfArrays() > 0:
                pointcloud_mapper.SetScalarModeToUsePointData()
                pointcloud_mapper.SetColorModeToDirectScalars()
                pointcloud_mapper.ScalarVisibilityOn()
            pointcloud_actor = vtk.vtkActor()
            pointcloud_actor.GetProperty().SetPointSize(3)
            pointcloud_actor.SetMapper(pointcloud_mapper)
            self._renderer.AddActor(pointcloud_actor)

    def _add_others(self):
        if self._others:
            for other in self._others:
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputData(other)
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetLineWidth(2.0)
                actor.GetProperty().SetColor(self._colors.GetColor3d('DarkKhaki'))
                self._renderer.AddActor(actor)

    def render(self):
        if _USE_SAMPLE_DATA:
            self._add_sample_data()
        else:
            self._add_meshes()
            self._add_pointcloud()
            self._add_others()
        orientation_widget = vtk.vtkCameraOrientationWidget()
        orientation_widget.SetParentRenderer(self._renderer)
        orientation_widget.On()
        self._renderer.AntiAliasedRenderer = True
        self._ren_win.Render()
        self._iren.Initialize()
        self._iren.Start()


if __name__ == '__main__':
    _USE_SAMPLE_DATA = True
    renderer = Renderer()
    renderer.render()

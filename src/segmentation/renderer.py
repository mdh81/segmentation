# Copyright (c) 2025 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from typing import Tuple, List


class Renderer:

    @property
    def meshes(self):
        return self._meshes

    @property
    def styles(self):
        return self._styles

    def __init__(self, size: Tuple[int, int] = (1024, 768), use_sample_data: bool = False):
        self._SIZE: Tuple[int, int] = size
        self._USE_SAMPLE_DATA: bool = use_sample_data

        self._ren_win = vtkRenderWindow()
        self._ren_win.SetSize(self._SIZE[0], self._SIZE[1])
        self._iren = vtkRenderWindowInteractor()
        self._iren.SetRenderWindow(self._ren_win)
        self._iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self._renderer = vtkRenderer()
        self._colors = vtkNamedColors()
        self._renderer.SetBackground(self._colors.GetColor3d('AliceBlue'))
        self._ren_win.AddRenderer(self._renderer)
        self._meshes: List[vtk.vtkPolyData] = []
        self._styles: List[vtk.vtkProperty] = []

    def _add_sample_data(self):
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetThetaResolution(25)
        sphere_source.SetPhiResolution(25)
        sphere_mapper = vtk.vtkPolyDataMapper()
        sphere_mapper.SetInputConnection(sphere_source.GetOutputPort())
        sphere_actor = vtk.vtkActor()
        sphere_actor.SetMapper(sphere_mapper)
        self._renderer.AddActor(sphere_actor)

    def _add_meshes(self):
        for mesh, prop in zip(self.meshes, self.styles):
            mesh_mapper = vtk.vtkPolyDataMapper()
            mesh_mapper.SetInputData(mesh)
            mesh_actor = vtk.vtkActor()
            mesh_actor.SetProperty(prop)
            mesh_actor.SetMapper(mesh_mapper)
            self._renderer.AddActor(mesh_actor)

    def render(self):
        if self._USE_SAMPLE_DATA:
            self._add_sample_data()
        else:
            self._add_meshes()
        self._ren_win.Render()
        self._iren.Initialize()
        self._iren.Start()


if __name__ == '__main__':
    Renderer._USE_SAMPLE_DATA = True
    renderer = Renderer()
    renderer.render()

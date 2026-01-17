# Copyright (c) 2026 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
from typing import List

import numpy as np
import pye57
import vtk
from math3d import vector3, vector4, matrix4, identity4

from segmentation.style import Color


class PointCloud:

    def __init__(self, e57: pye57.E57):
        self._e57 = e57
        self._coords: List[vector3] = []
        self._colors: List[Color] = []
        self._polydata = None
        self._transform: matrix4 = identity4()

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, transform: matrix4):
        self._transform = transform

    @property
    def points(self) -> List[vector3]:
        if not self._coords:
            self._read()
        return self._coords

    @property
    def colors(self) -> List[Color]:
        if not self._colors:
            self._read()
        return self._colors

    @property
    def polydata(self) -> vtk.vtkPolyData:
        if not self._polydata:
            self._assemble()
        return self._polydata

    def _read(self):
        if not self._colors or not self._coords:
            num_scans: int = self._e57.scan_count
            for i in range(num_scans):
                e57_data = self._e57.read_scan(i, colors=True, ignore_missing_fields=True)
                x: np.ndarray = e57_data['cartesianX']
                y: np.ndarray = e57_data['cartesianY']
                z: np.ndarray = e57_data['cartesianZ']
                for px, py, pz in zip(x, y, z, strict=True):
                    self._coords.append(vector3(px, py, pz))
                if 'colorRed' in e57_data:
                    r: np.ndarray = e57_data['colorRed']
                    g: np.ndarray = e57_data['colorGreen']
                    b: np.ndarray = e57_data['colorBlue']
                    for pr, pg, pb in zip(r, g, b, strict=True):
                        self._colors.append(Color(pr / 255, pg / 255, pb / 255))

    def _assemble(self) -> None:
        if not self._coords:
            self._read()
        self._polydata = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        cells = vtk.vtkCellArray()
        points.SetNumberOfPoints(len(self._coords))
        cells.AllocateEstimate(len(self._coords), 1)
        colors = vtk.vtkFloatArray() if self._colors else None
        if colors:
            colors.SetName('rgb')
            colors.SetNumberOfComponents(3)
            colors.SetNumberOfTuples(len(self._colors))
        for idx, coord in enumerate(self._coords):
            transformed_point: vector4 = self._transform * vector4(coord)
            points.SetPoint(idx, transformed_point.x, transformed_point.y, transformed_point.z)
            cells.InsertNextCell(1)
            cells.InsertCellPoint(idx)
            if colors:
                colors.SetTuple3(idx, self._colors[idx].r, self._colors[idx].g, self._colors[idx].b)
        self._polydata.SetPoints(points)
        self._polydata.SetVerts(cells)
        if colors:
            self._polydata.GetPointData().SetScalars(colors)

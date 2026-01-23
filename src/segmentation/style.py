# Copyright (c) 2025 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from dataclasses import dataclass
from typing import List, Tuple, Dict

from vtkmodules.vtkRenderingCore import vtkProperty


@dataclass(slots=True, frozen=True)
class Color:
    r: float
    g: float
    b: float

    def __str__(self):
        return f'{self.r}, {self.g}, {self.b}'


class Style:
    """
    A material that maps to ifc open shell's material definition
    """
    _AMBIENT_INTENSITY = 0.15
    _DIFFUSE_INTENSITY = 0.85
    _AMBIENT_COLOR = Color(0.75, 0.75, 0.75)

    def __init__(self, diffuse: Color, specular: Color, alpha: float):
        self._diffuse = diffuse
        self._specular = specular
        self._alpha = alpha

    @property
    def diffuse(self):
        return self._diffuse

    @property
    def specular(self):
        return self._specular

    @property
    def alpha(self):
        return self._alpha

    def __str__(self):
        return f'Diffuse = {self._diffuse},\n\tSpecular = {self._specular},\n\tAlpha = {self._alpha}'

    @property
    def style(self):
        prop = vtkProperty()
        prop.SetDiffuseColor(self.diffuse.r, self.diffuse.g, self.diffuse.b)
        prop.SetSpecularColor(self.specular.r, self.specular.g, self.specular.b)
        prop.SetOpacity(self.alpha)
        prop.SetAmbient(Style._AMBIENT_INTENSITY)
        prop.SetDiffuse(Style._DIFFUSE_INTENSITY)
        prop.SetAmbientColor(Style._AMBIENT_COLOR.r, Style._AMBIENT_COLOR.g, Style._AMBIENT_COLOR.b)
        return prop


class Styles:
    """
    Maintains a list of style assignments originally in the form of 1 to N triangle indices
    Once all style assignments are complete, and request to assemble the styles is made, it
    compresses the triangle indices into a sequence of contiguous ranges
    """

    def __init__(self):
        self._styles: Dict[Style, List[Tuple[int, int]]] = {}
        self._assignments: Dict[Style, List[int]] = {}

    @property
    def list(self) -> List[Style]:
        if not self._styles:
            self._assemble()
        return list(self._styles.keys())

    def __str__(self):
        if not self._styles:
            self._assemble()
        s = '\n'
        for style, face_ids in self._styles.items():
            s += f'\t{style}\n'
            for start, end in face_ids:
                s += f'\tAssigned to faces: [{start},{end}]\n'
        return s

    def get_faces(self, style: Style) -> List[Tuple[int, int]]:
        if not self._styles:
            self._assemble()
        return self._styles[style]

    def add(self, style: Style) -> None:
        self._assignments[style] = []

    def assign(self, style: Style, face_id: int) -> None:
        self._assignments.setdefault(style, []).append(face_id)

    def _assemble(self):
        self._styles.clear()
        for style, face_ids in self._assignments.items():
            self._styles[style] = Styles._make_ranges(face_ids)
        self._assignments.clear()

    @staticmethod
    def _make_ranges(face_ids: List[int]) -> List[Tuple[int, int]]:
        ranges = []
        start = 0
        for index, _ in enumerate(face_ids):
            if index == 0:
                continue
            if face_ids[index] != face_ids[index - 1] + 1:
                ranges.append((face_ids[start], face_ids[index - 1]))
                start = index
        ranges.append((face_ids[start], face_ids[-1]))
        return ranges

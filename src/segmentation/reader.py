# Copyright (c) 2025 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import multiprocessing
import os.path
import sys
from typing import Optional, List, Dict, Tuple

import ifcopenshell as ifc
import ifcopenshell.geom
import pye57
from math3d import Vector3
from rich import print

from segmentation.mesh import TriangleMesh, Triangle
from segmentation.pointcloud import PointCloud
from segmentation.renderer import Renderer, MeshRep
from segmentation.style import Style, Color, Styles


class IFCReader:
    """
    Reads an IFC file using ifcopenshell. Converts each IFC object into
    @:type RenderObject
    """

    IGNORED_ENTITIES = ('IfcOpeningElement', 'IfcSpace',)

    def __init__(self, ifc_file_name: str):
        if not os.path.exists(os.path.normpath(ifc_file_name)):
            raise FileNotFoundError(f'{ifc_file_name} is not a valid file')

        self._ifc_file: str = ifc_file_name
        self._model: Optional[ifc.file] = None
        self._meshes: List[TriangleMesh] = []
        self._styles: Optional[Dict[int, Style]] = None

    @property
    def file(self) -> str:
        return self._ifc_file

    @property
    def model(self) -> Optional[ifc.file]:
        if not self._model:
            self._read()
        return self._model

    @property
    def meshes(self) -> List[TriangleMesh]:
        if not self._meshes:
            self._read()
        return self._meshes

    def summary(self, detailed: bool = False) -> None:
        print(f'File name: [yellow]{self.file}[/yellow]')
        print(f'Schema: [bold yellow]{self.model.schema_identifier}[bold yellow]')
        print(f'Number of meshes: {len(self.meshes)}')
        if detailed:
            for m in self._meshes:
                print(f'{m}')

    def _read(self) -> None:
        self._model = ifc.open(self._ifc_file)

        settings = ifc.geom.settings()
        iterator = ifc.geom.iterator(settings, self._model,
                                     multiprocessing.cpu_count())

        if iterator.initialize():
            while True:
                shape = iterator.get()
                if shape.type not in IFCReader.IGNORED_ENTITIES:
                    self._meshes.append(IFCReader._make_trimesh(shape))
                if not iterator.next():
                    break

    @staticmethod
    def _make_trimesh(shape: ifc.ifcopenshell_wrapper.TriangulationElement):
        trimesh = TriangleMesh(shape.type)
        vertices = shape.geometry.verts
        faces = shape.geometry.faces
        for i in range(0, len(vertices), 3):
            trimesh.vertices.append(Vector3(vertices[i], vertices[i + 1], vertices[i + 2]))
        for i in range(0, len(faces), 3):
            trimesh.triangles.append(Triangle(faces[i], faces[i + 1], faces[i + 2]))
        IFCReader._style_mesh(trimesh, shape.geometry.materials, shape.geometry.material_ids)
        trimesh.transform = shape.transformation.matrix
        return trimesh

    @staticmethod
    def _style_mesh(trimesh: TriangleMesh, ifc_styles: Tuple[ifc.ifcopenshell_wrapper.style, ...],
                    ifc_style_by_face_id: Tuple[int, ...]) -> None:
        styles_dict = IFCReader._process_styles(ifc_styles)
        mesh_styles: Styles = Styles()
        for face_id, style_id in enumerate(ifc_style_by_face_id):
            mesh_styles.assign(styles_dict[style_id], face_id)
        trimesh.styles = mesh_styles

    @staticmethod
    def _process_styles(ifc_styles: Tuple[ifc.ifcopenshell_wrapper.style, ...]) -> Dict[
        int, Style]:
        styles: Dict[int, Style] = {}
        for index in range(len(ifc_styles)):
            ifc_style = ifc_styles[index]
            diffuse = Color(ifc_style.diffuse.r(), ifc_style.diffuse.g(), ifc_style.diffuse.b())
            specular = Color(ifc_style.specular.r(), ifc_style.specular.g(), ifc_style.specular.b())
            styles[index] = Style(diffuse, specular,
                                  1 if not ifc_style.has_transparency() else 1 - ifc_style.transparency)
        return styles


class E57Reader:

    def __init__(self, e57_file: str):
        self._e57_file = e57_file
        self._pointcloud: PointCloud | None = None

    def summary(self) -> None:
        print(f'Point cloud file {self._e57_file}')
        print(f'Number of points: {len(self.pointcloud.points)}')

    @property
    def pointcloud(self) -> PointCloud:
        if self._pointcloud is None:
            data = pye57.E57(self._e57_file)
            self._pointcloud = PointCloud(data)
        return self._pointcloud


if __name__ == '__main__':

    if len(sys.argv) != 2:
        raise RuntimeError('File to read is not specified')

    renderer = Renderer()

    if sys.argv[1].endswith('.ifc'):
        reader: IFCReader = IFCReader(sys.argv[1])
        reader.summary()
        for mesh in reader.meshes:
            renderer.meshes.append(MeshRep(mesh.polydata, mesh.category, mesh.get_lut_and_prop()))
    elif sys.argv[1].endswith('.e57'):
        reader: E57Reader = E57Reader(sys.argv[1])
        reader.summary()
        renderer.pointcloud = reader.pointcloud.polydata

    renderer.render()

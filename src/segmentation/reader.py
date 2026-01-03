import multiprocessing
import os.path
import sys
from typing import Optional, List, Dict, Tuple, Set

import vtk
from rich import print
import ifcopenshell as ifc
import ifcopenshell.geom
from segmentation.mesh import TriangleMesh, Triangle
from math3d import vector3
from segmentation.renderer import Renderer
from segmentation.style import Style, Color, Styles


class IFCReader:
    """
    Reads an IFC file using ifcopenshell. Converts each IFC object into
    @:type RenderObject
    """

    IGNORED_ENTITIES = ('IfcOpeningElement',)

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
    def meshes(self):
        if not self._meshes:
            self._read()
        return self._meshes

    def summary(self):
        print(f'File name: [yellow]{self.file}[/yellow]')
        print(f'Schema: [bold yellow]{self.model.schema_identifier}[bold yellow]')
        print(f'Number of meshes: {len(self.meshes)}')
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
            trimesh.vertices.append(vector3([vertices[i], vertices[i + 1], vertices[i + 2]]))
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


if __name__ == '__main__':

    if len(sys.argv) != 2:
        raise RuntimeError(f'Ifc file not specified')

    reader: IFCReader = IFCReader(sys.argv[1])
    reader.summary()

    renderer = Renderer()
    for mesh in reader.meshes:
        renderer.meshes.append(mesh.polydata)
        renderer.styles.append(mesh.styles.list[0].style)
    renderer.render()

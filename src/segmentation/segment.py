# Copyright (c) 2026 Murali Dhanakoti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from argparse import ArgumentParser
from typing import Tuple

import math3d
from segmentation.reader import E57Reader, IFCReader
from segmentation.renderer import Renderer, MeshRep


def _setup_args() -> ArgumentParser:
    parser = ArgumentParser(
        prog='Point cloud segmentation',
        epilog='''
        This program segments a point cloud using a reference model.
        To place the point cloud in the reference model's frame, specify the point cloud to reference model transform
        via the -t option
        '''
    )
    parser.add_argument('reference', help='reference model in IFC format')
    parser.add_argument('pointcloud', help='point cloud to segment in E57 format')
    parser.add_argument('-t', '--transform', help='point cloud to reference model transform (in column major order)')
    return parser


def _parse_args(parser: ArgumentParser) -> Tuple[str, str, math3d.matrix4]:
    args = parser.parse_args()
    return (args.reference, args.pointcloud,
            math3d.identity4() if not args.transform else math3d.matrix4(args.transform, math3d.order.col_major))


def main():
    parser = _setup_args()
    ifc_ref, e57_pc, pc_transform = _parse_args(parser)
    print(f'Segmenting point cloud {e57_pc} using {ifc_ref}')
    print(f'Point cloud to reference model transform\n{pc_transform}')
    pc_reader = E57Reader(e57_pc)
    ifc_reader = IFCReader(ifc_ref)
    ifc_reader.summary()
    pc_reader.summary()
    renderer = Renderer()
    for mesh in ifc_reader.meshes:
        renderer.meshes.append(MeshRep(mesh.polydata, mesh.category, mesh.get_lut_and_prop()))
    renderer.pointcloud = pc_reader.pointcloud.polydata
    renderer.render()

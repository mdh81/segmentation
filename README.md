### Segment point clouds using IFC models

This is a prototype for a point cloud segmentation solution

The point cloud and reference model are expected to be twins of each other -- reference model is
schematic model, point cloud is the reality-capture version of the same model.
As such, segmentation only works when the two models are aligned already or if a transform to align
point cloud with the reference model is provided

#### Run

```bash
$ brew install poetry #if poetry not installed
$ cd <this project directory>
$ poetry install
$ source .venv/bin/activate
$ segmentation --help 
```
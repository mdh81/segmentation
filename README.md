### Segment point clouds using IFC models

This is a prototype for a point cloud segmentation solution

The point cloud and IFC are expected to be twins of each other -- IFC is
schematic model, point cloud is the reality-capture version of the same model.
As such, segmentation only works when the two models are aligned already

```bash
$ brew install poetry #if poetry not installed
$ cd <this project directory>
$ poetry install
$ source .venv/bin/activate
```

Segmentation is WIP, at the moment, you can run individual modules within the segmentation package to exercise/test
various functionalities 

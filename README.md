### Point cloud segmentation

This is a prototype for a point cloud segmentation solution

The point cloud and reference model are expected to be twins of each other -- reference model is
schematic model, point cloud is the reality-capture version of the same model.
As such, segmentation only works when the two models are aligned already or if a transform to align
point cloud with the reference model is provided

#### Run

##### Install python 3.13 (if not installed already)

```bash
$ brew install uv # if uv is not installed
$ uv python install 3.13
$ uv python update-shell
```

Use of uv is not mandatory. Use pyenv or other preferred python version management tool, the only
requirement is that poetry in the below steps is able to find 3.13 to set up the project

#### Install project

```bash 
$ brew install poetry # if poetry is not installed
$ cd <this project directory>
$ poetry env use python3.13
# Alternative 1
$ source .venv/bin/activate 
$ poetry install
$ segmentation --help 
# Alternative 2 (if there is no need to experiment with the package in the interpreter) 
$ poetry install
$ poetry run segmentation --help
```
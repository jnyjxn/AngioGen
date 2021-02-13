## Usage
You can either run the entire generation process with one command, or run each of the three stages of generation separately.
### A. Run entire process
`python src/generate.py config/custom.yaml`

Note: offscreen rendering is possible, for example:

`PYOPENGL_PLATFORM=egl python src/generate.py config/custom.yaml`

For more info, please follow the instructions [here](https://pyrender.readthedocs.io/en/latest/examples/offscreen.html).

### B. Run each step separately
#### 1. First generate the vascular network graph.

`python src/generate_graph.py config/custom.yaml`

#### 2. Then generate the 3D data (e.g. meshes, pointclouds, etc.).

`python src/generate_three_d.py config/custom.yaml`

#### 3. Finally generate the 2D data (e.g. images, camera matrices, depth maps, etc.).

`python src/generate_two_d.py config/custom.yaml`

Note: offscreen rendering is possible, for example:

`PYOPENGL_PLATFORM=egl python src/generate_two_d.py config/custom.yaml`

For more info, please follow the instructions [here](https://pyrender.readthedocs.io/en/latest/examples/offscreen.html).
## Usage
1. First generate the vascular networks.

`python src/generate_networks.py config/your_config.yaml`

2. Then generate the meshes.

`src/external/[Your Blender Folder Name]/blender --background -P src/generate_meshes.py -- config/default.yaml`

Don't omit the '--'!
# Installation Instructions
## Installing AngioGen
1. Clone the repository
```
git clone https://github.com/jnyjxn/AngioGen.git
```
2. Install the requirements
```
cd ./AngioGen
pip install -r requirements.txt
```

## Installing VascuSynth
1. Move to the VascuSynth folder
```
cd src/graph/lib/VascuSynth/bin
```
2. Run CMake
```
cmake ..
```
3. Compile
```
make
```

## Installing Blender
### Downloading Blender
1. Download Blender for free from https://www.blender.org/ and place the entire folder in `src/external`.

### Installing dependencies into Blender's Python
Blender ships with its own Python set up. This means dependencies have to be installed directly within Blender's own Python environment.

1. Find the location of Python within Blender. It should be at 
`[BLENDER_ROOT]/[2.xx]/python/`, where BLENDER_ROOT is the parent directory of the download, and 2.xx is the version you have dowloaded (such as 2.90).
2. Change directory into that folder using cd, for example:

`cd src/external/blender-2.90.1-linux64/2.90/python`

3. Install pip *within* Blender's Python:
- Linux/Mac:
`./bin/python -m ensurepip`
- Windows:
`./bin/python.exe -m ensurepip`

4. Install required packages:
- Linux/Mac:
`./bin/pip3 install pyyaml scipy`
- Windows:
`./bin/pip3.exe install pyyaml scipy`
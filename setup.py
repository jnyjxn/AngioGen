try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages
from distutils.extension import Extension
from Cython.Build import cythonize
# from torch.utils.cpp_extension import BuildExtension
import numpy

# Get the numpy include directory.
numpy_include_dir = numpy.get_include()

# triangle hash (efficient mesh intersection)
triangle_hash_module = Extension(
    'src.three_d.lib.triangle_hasher.triangle_hash',
    sources=[
        'src/three_d/lib/triangle_hasher/triangle_hash.pyx'
    ],
    libraries=['m'],  # Unix-like specific
    include_dirs=[numpy_include_dir],
    language="c++"
)

# voxelization (efficient mesh voxelization)
voxelize_module = Extension(
    'src.three_d.lib.libvoxelize.voxelize',
    sources=[
        'src/three_d/lib/libvoxelize/voxelize.pyx'
    ],
    libraries=['m']  # Unix-like specific
)

# Gather all extension modules
ext_modules = [
    triangle_hash_module,
    voxelize_module
]

setup(
    ext_modules=cythonize(ext_modules),
    packages=find_packages(),
    # cmdclass={
    #     'build_ext': BuildExtension
    # }
)
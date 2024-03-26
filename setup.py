from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "superbased58",
        sources=["superbased58.pyx"],
        include_dirs=["impl/firedancer/src/ballet/base58"],
        library_dirs=["impl/lib"],
        libraries=["fd_ballet"],
    ),
]

setup(
    ext_modules=cythonize(extensions),
)

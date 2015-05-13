"""
Usage:
    python csetup.py build_ext --inplace

    import cmplay
    cmplay.main(path)
"""
from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("cmplay.pyx")
)

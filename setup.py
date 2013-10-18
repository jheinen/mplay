"""
Usage:
    python setup.py py2app
"""
from setuptools import setup

setup(
    app=["mplay.py"],
    requires = [
        'pyobjc-framework-cocoa',
        'PyOpenGL'
    ], 
    setup_requires=["py2app"],
)
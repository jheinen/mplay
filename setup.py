"""
Usage:
    python setup.py py2app
"""
from setuptools import setup

COPYRIGHT = 'Copyright 2013 Josef Heinen'

setup(
    app=['mplay.py'],
    data_files=['mixer.ppm'],
    options={'py2app': {'argv_emulation': True,
                        'iconfile': 'mplay.icns',
                        'plist': {'CFBundleIdentifier': 'de.josefheinen.mplay',
                                  'CFBundleVersion': '1.0.1',
                                  'CFBundleShortVersionString': '1.0.1',
                                  'NSHumanReadableCopyright': COPYRIGHT}}},
    setup_requires=['py2app', 'pyobjc-framework-cocoa', 'PyOpenGL']
)

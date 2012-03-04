from distutils.core import setup
import py2exe

setup(
    console=['platform.py'],
    zipfile=None,
    options = {
        "py2exe": {
            "compressed": True,
            "optimize": 2,
            "bundle_files": 1,
            "excludes": ["doctest", "pdb", "unittest", "difflib", "inspect"],
            "dll_excludes": ['w9xpopen.exe'],
            "unbuffered": True
        }
    },
)

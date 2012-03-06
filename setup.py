from distutils.core import setup
import py2exe

setup(
    name='robopoker-sdk-src',
    version='0.24',
    description='Poker engine and bot development kit',
    url='http://robopoker.org',
    download_url='http://robopoker.org.vbo.dev.vbo.name/about/sdk/',
    packages=['robopoker', 'robopoker.handstate'],
    scripts=['platform.py'],
    data_files=[('',['create.bat', 'play.bat', 'create.sh',  'play.sh', 'hand_players.list'])],

    zipfile=None,
    console=['platform.py'],
    options = {
        "py2exe": {
            "compressed": True,
            "optimize": 2,
            "bundle_files": 1,
            "excludes": ["doctest", "pdb", "unittest", "difflib", "inspect"],
            "dll_excludes": ['w9xpopen.exe'],
            "unbuffered": True,
        }
    },
)

from distutils.core import setup
import py2exe

setup(
    name='robopoker-sdk-src',
    version='0.272',
    description='Poker engine and SDK for RoboPoker project',
    url='http://robopoker.org',
    author='RoboPoker Team',
    author_email='robopoker@robopoker.org',
    download_url='http://robopoker.org/about/sdk/',
    packages=['robopoker', 'robopoker.handstate'],
    scripts=['platform.py'],
    data_files=[('',[
        'create.bat', 'play.bat',
        'create.sh',  'play.sh',
        'hand_players.list',
        'LICENSE', 'README.md'
    ])],

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

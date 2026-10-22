"""Build the separate Windows 7 SP1 x64 candidate with Python 3.7.9.

The modern installer must continue to use tools/build.py. See LEGACY.md for
the historical toolchain and the distinction between CI and Windows 7 tests.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

import importlib_metadata

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build-legacy'
DIST = ROOT / 'dist-legacy'


def check_toolchain():
    if sys.platform != 'win32' or sys.version_info[:3] != (3, 7, 9):
        raise RuntimeError('Legacy builds require Windows and Python 3.7.9 x64')
    import struct
    if struct.calcsize('P') != 8:
        raise RuntimeError('Legacy builds require a 64-bit Python interpreter')
    if importlib_metadata.version('pyinstaller') != '3.6':
        raise RuntimeError('Legacy builds require the pinned PyInstaller 3.6')


def collect_notices(package):
    """Keep the actual Python, Tcl/Tk and PyInstaller license texts."""
    destination = package / 'licenses'
    destination.mkdir(exist_ok=True)

    def copy_required(candidates, name):
        for candidate in candidates:
            if candidate.is_file():
                shutil.copy2(candidate, destination / name)
                return
        raise RuntimeError('Missing required distribution notice: ' + name)

    base = Path(sys.base_prefix)
    copy_required((base / 'LICENSE.txt', base / 'LICENSE'), 'Python-LICENSE.txt')
    import tkinter
    tcl_library = Path(tkinter.Tcl().eval('info library'))
    copy_required((tcl_library / 'license.terms',), 'Tcl-LICENSE.txt')
    copy_required(tuple(candidate / 'license.terms'
                        for candidate in tcl_library.parent.glob('tk*')),
                  'Tk-LICENSE.txt')
    distribution = importlib_metadata.distribution('pyinstaller')
    candidates = []
    for entry in distribution.files or ():
        if entry.name in ('COPYING.txt', 'LICENSE', 'LICENSE.txt'):
            candidates.append(Path(distribution.locate_file(entry)))
    import PyInstaller
    candidates.extend((Path(PyInstaller.__file__).parent / 'COPYING.txt',
                       Path(PyInstaller.__file__).parent.parent / 'COPYING.txt'))
    copy_required(candidates, 'PyInstaller-COPYING.txt')


def windows_version_file(version):
    parts = tuple(map(int, version.split('.'))) + (0,)
    path = WORK / 'windows-version.txt'
    path.parent.mkdir(exist_ok=True)
    path.write_text('''VSVersionInfo(
  ffi=FixedFileInfo(filevers={parts!r}, prodvers={parts!r},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'Triliza Legacy'),
    StringStruct('FileVersion', '{version}'),
    StringStruct('InternalName', 'TrilizaLegacy'),
    StringStruct('OriginalFilename', 'TrilizaLegacy.exe'),
    StringStruct('ProductName', 'Triliza Legacy'),
    StringStruct('ProductVersion', '{version}')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
'''.format(parts=parts, version=version), encoding='utf-8')
    return path


def build():
    check_toolchain()
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must contain a numeric major.minor.patch version')
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
            '--windowed', '--onedir', '--name', 'TrilizaLegacy',
            '--distpath', str(DIST), '--workpath', str(WORK),
            '--specpath', str(WORK),
            '--add-data', str(ROOT / 'assets') + ';assets',
            '--add-data', str(ROOT / 'VERSION') + ';.',
            '--hidden-import', 'winsound',
            '--icon', str(ROOT / 'assets' / 'app.ico'),
            '--version-file', str(windows_version_file(version)),
            str(ROOT / 'main.py')]
    subprocess.run(args, cwd=str(ROOT), check=True)
    package = DIST / 'TrilizaLegacy'
    for name in ('README.md', 'THIRD_PARTY.md', 'LEGACY.md', 'VERSION'):
        shutil.copy2(ROOT / name, package / name)
    collect_notices(package)
    print('Legacy distribution: ' + str(package))
    print('Compile with Inno Setup 6.2.2: ISCC.exe /DAppVersion=' + version +
          ' installer\\windows7.iss')


if __name__ == '__main__':
    build()

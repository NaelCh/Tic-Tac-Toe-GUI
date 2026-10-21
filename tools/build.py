"""Build on the target OS: python tools/build.py.

Windows: bundle the complete runtime first, then compile installer/windows.iss
with Inno Setup 6. See the release workflow for tested installation commands.
"""
from importlib import metadata
from pathlib import Path
import re
import shutil
import subprocess
import sys
import sysconfig

ROOT = Path(__file__).resolve().parents[1]


def collect_notices(package):
    """Preserve licenses shipped with the build's Python/Tcl/Tk packages."""
    destination = package / 'licenses'
    destination.mkdir(exist_ok=True)

    def copy_first(candidates, name):
        for candidate in candidates:
            if candidate.is_file():
                shutil.copy2(candidate, destination / name)
                return

    base = Path(sys.base_prefix)
    copy_first((base / 'LICENSE.txt', base / 'LICENSE',
                Path(sysconfig.get_path('stdlib')) / 'LICENSE.txt',
                Path('/usr/share/doc') / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'copyright'),
               'Python-LICENSE.txt')
    import tkinter
    tcl_library = Path(tkinter.Tcl().eval('info library'))
    copy_first((tcl_library / 'license.terms', Path('/usr/share/doc/libtcl8.6/copyright')),
               'Tcl-LICENSE.txt')
    tk_licenses = [candidate / 'license.terms' for candidate in tcl_library.parent.glob('tk*')]
    copy_first((*tk_licenses, Path('/usr/share/doc/libtk8.6/copyright')), 'Tk-LICENSE.txt')
    distribution = metadata.distribution('pyinstaller')
    for entry in distribution.files or ():
        if entry.name in ('COPYING.txt', 'LICENSE', 'LICENSE.txt'):
            source = Path(distribution.locate_file(entry))
            if source.is_file():
                shutil.copy2(source, destination / f'PyInstaller-{entry.name}')
    # Distro binaries can include additional system-library notices.
    if sys.platform.startswith('linux') and shutil.which('dpkg-query'):
        packages = set()
        for binary in (package / '_internal').glob('*.so*'):
            library = Path('/usr/lib/x86_64-linux-gnu') / binary.name
            if library.exists():
                lookup = subprocess.run(['dpkg-query', '-S', str(library)],
                                        text=True, capture_output=True, check=False)
                if lookup.returncode == 0:
                    packages.add(lookup.stdout.split(': ')[0].split(':')[0])
        for name in packages:
            copy_first((Path('/usr/share/doc') / name / 'copyright',), f'{name}-copyright.txt')
        for name in ('GPL-2', 'GPL-3', 'LGPL-2', 'LGPL-2.1', 'LGPL-3'):
            copy_first((Path('/usr/share/common-licenses') / name,), name)


def windows_version_file(version):
    """PyInstaller's Windows version resource uses a four-part numeric version."""
    parts = tuple(map(int, version.split('.'))) + (0,)
    path = ROOT / 'build' / 'windows-version.txt'
    path.parent.mkdir(exist_ok=True)
    path.write_text(f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={parts!r}, prodvers={parts!r},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'Τρίλιζα'),
    StringStruct('FileVersion', '{version}'),
    StringStruct('InternalName', 'Triliza'),
    StringStruct('OriginalFilename', 'Triliza.exe'),
    StringStruct('ProductName', 'Τρίλιζα'),
    StringStruct('ProductVersion', '{version}')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
''', encoding='utf-8')
    return path


def build():
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must contain a numeric major.minor.patch version')
    import os
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
            '--windowed', '--onedir', '--name', 'Triliza',
            '--distpath', str(ROOT / 'dist'), '--workpath', str(ROOT / 'build'),
            '--specpath', str(ROOT / 'build'),
            '--add-data', f'{ROOT / "assets"}{os.pathsep}assets',
            '--add-data', f'{ROOT / "VERSION"}{os.pathsep}.']
    if sys.platform == 'win32':
        args.extend(('--hidden-import', 'winsound', '--icon', str(ROOT / 'assets' / 'app.ico'),
                     '--version-file', str(windows_version_file(version))))
    args.append(str(ROOT / 'main.py'))
    subprocess.run(args, cwd=ROOT, check=True)
    package = ROOT / 'dist' / 'Triliza'
    for name in ('README.md', 'THIRD_PARTY.md', 'VERSION'):
        shutil.copy2(ROOT / name, package / name)
    if (ROOT / 'docs' / 'screenshot.png').is_file():
        (package / 'docs').mkdir(exist_ok=True)
        shutil.copy2(ROOT / 'docs' / 'screenshot.png', package / 'docs' / 'screenshot.png')
    collect_notices(package)
    print(f'Distribution folder: {package}. Ship the entire folder, including _internal.')
    if sys.platform == 'win32':
        print(f'Installer: ISCC.exe /DAppVersion={version} installer\\windows.iss')


if __name__ == '__main__':
    build()

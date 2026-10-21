"""Build on the OS you intend to distribute to: python tools/build.py."""
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                '--windowed', '--onedir', '--name', 'Triliza',
                '--distpath', str(root / 'dist'), '--workpath', str(root / 'build'),
                '--specpath', str(root / 'build'), str(root / 'main.py')],
               cwd=root, check=True)
package = root / 'dist' / 'Triliza'
for name in ('README.md', 'COMMERCIAL.md', 'THIRD_PARTY.md'):
    shutil.copy2(root / name, package / name)
print(f'Distribution folder: {package}. Ship the entire folder, including _internal.')

# Τρίλιζα Legacy — Windows 7 SP1 x64

This is a separate experimental installer for 64-bit Windows 7 Service Pack 1.
It contains the game, Python, Tk and sound files, so the player does not need
to install Python. The Windows 10/11 installer remains the recommended edition
on a current computer. No separate repository is needed.

## Download and install

Open the repository's **Releases** page and select the prerelease whose tag is
`legacy-v1.3.3` (or a newer `legacy-v…` tag). Download
`Triliza-1.3.3-Windows7-SP1-x64-Setup.exe`, run it, then open **Τρίλιζα Legacy**
from the Start menu. A release is published only after the installer passes
the automated Windows build, installation, game smoke test and removal checks.

The Legacy edition uses its own installation directory and uninstall entry.
It can coexist with the Windows 10/11 edition. Future Legacy installers upgrade
the same Legacy installation. It does not automatically update itself.

## Compatibility and verification

The target is **Windows 7 SP1, 64-bit, with Microsoft's available system and
Universal CRT updates installed**. Windows 7 without SP1 and 32-bit Windows
are outside this build's target. The installer does not download or silently
change system updates.

The historical build uses **Python 3.7.9 x64**, **PyInstaller 3.6** and
**Inno Setup 6.2.2**. Python 3.7 supports Windows Vista and later; PyInstaller
3.6 documents Windows XP and later and supports Python 3.7. Inno Setup 6.2.2
documents support for Windows 7. The newer tools used for the main edition
have different Windows requirements, so installing the main edition on Windows
7 does not provide the same compatibility.

**A successful CI run is not a Windows 7 compatibility certification.** GitHub's
hosted test machine runs Windows Server 2022. It checks the frozen application,
keyboard/keypad mapping, game round, bundled audio, install and uninstall while
Python is absent from PATH. No real Windows 7 machine or VM is available in
this development environment. This Legacy candidate therefore still needs the
following checks on the intended Windows 7 SP1 computer before being sold as
Windows 7 compatible:

1. Install as a normal user on a machine without Python installed.
2. Launch from the Start menu and optional desktop shortcut.
3. Play a round at each difficulty and a local two-player round.
4. Check numeric keypad 7/8/9 at the top, 4/5/6 in the middle and 1/2/3 below.
5. Check click, win, loss and draw sounds, sound mute and window resizing.
6. Install the same or a newer Legacy build again, then uninstall it.

Python 3.7 and Windows 7 no longer receive normal security support. Pinning
historical tools provides a compatibility candidate; it does not restore vendor
security support. The Legacy game remains an offline desktop application.

## Build and publish

Use a Windows machine with the x64 Python 3.7.9 distribution and Tk installed:

```powershell
python -m pip install --upgrade pip==23.3.2
python -m pip install --requirement requirements-legacy-build.txt
python -m unittest discover -s tests -v
python tools/build_legacy.py
& 'C:\path\to\Inno Setup 6.2.2\ISCC.exe' /DAppVersion=1.3.3 installer\windows7.iss
```

The output directory is `dist-legacy`; the main build's `dist` is untouched.
Always read the current `VERSION` instead of reusing the example version.
The workflow downloads the pinned Inno installer from the official publisher
and requires a valid Authenticode signature from **Jordan Russell** before
running it. It also records the downloaded compiler's SHA256. Signature
verification is never disabled to work around an unavailable download.

The **Windows 7 Legacy installer** workflow can be run manually to produce
an Actions artifact. Push `legacy-v<matching VERSION>` to publish it as a
GitHub prerelease after testing. It uses a distinct tag prefix so the modern
Windows release workflow is not triggered. Published installer files have
a companion `.sha256` checksum. Successful publication also creates an
immutable `windows7-installer/<release-tag>` Git receipt that explicitly
records `windows7_runtime_verified: false`; failure diagnostics use
`windows7-installer-error/<release-tag>`.

Upstream compatibility references:

- [Python 3.7 Windows documentation](https://docs.python.org/3.7/using/windows.html)
- [PyInstaller 3.6 requirements](https://pyinstaller.org/en/v3.6/requirements.html)
- [PyInstaller 3.6 supported Python versions](https://github.com/pyinstaller/pyinstaller/tree/v3.6)
- [Inno Setup 6.2.2 documentation source](https://github.com/jrsoftware/issrc/blob/is-6_2_2/ISHelp/isetup.xml)

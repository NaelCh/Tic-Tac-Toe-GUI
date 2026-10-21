# Third-party components

The source game uses Python's standard library (Tkinter, dataclasses, functools,
random). It contains no downloaded artwork or bundled custom fonts.
A frozen distribution includes Python, Tcl/Tk and platform-dependent libraries.

- Python: PSF License and bundled component notices — https://docs.python.org/3/license.html
- Tcl/Tk: permissive Tcl/Tk license — https://www.tcl-lang.org/software/tcltk/license.html
- PyInstaller: GPL with a bootloader exception permitting commercial distribution
  of generated applications — https://pyinstaller.org/en/stable/license.html
- Linux builds may bundle libraries under additional licenses, including LGPL.
  Inventory the actual binaries before commercial release, preserve their license
  and copyright texts, and provide applicable source/relinking information.

This file identifies dependencies; it does not replace their complete license
texts or grant rights to the original game repository. Retain upstream notices
and audit the exact target-platform package rather than assuming licenses from
another operating system apply. Build-tool dependencies are listed separately
in requirements-build.txt and are not game runtime dependencies.

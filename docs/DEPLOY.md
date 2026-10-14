# DiffSeis SU Viewer deployment

## Required build packages

On Debian, Ubuntu, or Linux Mint, install:

```bash
sudo apt update
sudo apt install build-essential python3 python3-pip python3-tk wget
```

These packages provide:

- `make`, required by the `Makefile`
- Python 3 and Tkinter, required by the application and PyInstaller
- `pip`, required to install PyInstaller
- `wget`, used to download the application icon, `appimagetool`, and its
  runtime

`curl` may be used instead of `wget`:

```bash
sudo apt install build-essential python3 python3-pip python3-tk curl
```

Install PyInstaller in the Python environment used for the build:

```bash
python3 -m pip install --user pyinstaller
```

If the system blocks `pip --user`, use a virtual environment instead:

```bash
python3 -m venv .venv-build
source .venv-build/bin/activate
python -m pip install --upgrade pip pyinstaller
```

## Build the AppImage

Run the command from the repository root:

```bash
make deploy
```

The Makefile builds the PyInstaller executable, prepares `AppDir`, downloads
the generic PNG icon, downloads `appimagetool` when needed, and creates:

```text
SUviewer-$(uname -m).AppImage
```

For an x86_64 machine, the output is:

```text
SUviewer-x86_64.AppImage
```

Run it with:

```bash
./SUviewer-x86_64.AppImage
```

## Compatibility and runtime requirements

Build the AppImage on the oldest Linux distribution you intend to support.
The target machine needs a compatible or newer `glibc`; AppImage does not
bundle glibc.

The target machine does not need Python or `python3-tk`. It does need a
graphical desktop session and Seismic Unix with these commands available:

```bash
which surange
which suximage
```

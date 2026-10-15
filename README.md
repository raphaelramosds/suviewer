# SUviewer

![exemplo](assets/exemplo.jpg)

## What is SUviewer?

Tkinter launcher for displaying Seismic Unix files with `suximage`.

## Installation

Download the AppImage from the *releases* and run it by following the instructions below

```bash
chmod +x SUviewer-x86_64.AppImage
./SUviewer-x86_64.AppImage
```

## Development

Refer to [DEPLOY.md](docs/DEPLOY.md) for instructions on how to build the AppImage from source.

Install Seismic Unix first and ensure `suximage` is available on your `PATH`, then run:

```bash
python suviewer/app.py
```

## Displaying multiple images

Click **Add files...** and select one or more `.su` files (use Ctrl/Shift while
selecting). Each selected file is opened in its own `suximage` window when you
click **Display with suximage**. You can add more files without closing the
windows that are already open. Use **Remove selected** or **Clear files** to
manage the list. Click **Close all images** to close every open `suximage`
window at once.

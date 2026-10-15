"""Select a Seismic Unix file and display it with ``suximage``."""

from __future__ import annotations

import math
import shutil
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional


class SUImageViewer:
    """Small Tkinter front end for the Seismic Unix ``suximage`` command."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.input_file = None
        self.file_var = tk.StringVar()
        self.perc_var = tk.StringVar(value="99")
        self.status_var = tk.StringVar(value="Select a .su file to display.")
        self.surange_text = None
        self._build_window()

    def _build_window(self) -> None:
        self.root.title("SU Image Viewer")
        self.root.minsize(560, 190)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        frame = ttk.Frame(self.root, padding=16)
        frame.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Seismic Unix file:").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Entry(frame, textvariable=self.file_var).grid(
            row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 12)
        )
        ttk.Button(frame, text="Browse...", command=self.choose_file).grid(
            row=1, column=1, sticky="ew", pady=(4, 12)
        )
        ttk.Label(frame, text="Amplitude percentile (perc):").grid(
            row=2, column=0, sticky="w", pady=(0, 12)
        )
        ttk.Spinbox(
            frame,
            from_=0.01,
            to=100,
            increment=0.5,
            textvariable=self.perc_var,
            width=10,
        ).grid(row=2, column=1, sticky="w", pady=(0, 12))
        ttk.Button(frame, text="Display with suximage", command=self.display).grid(
            row=3, column=0, columnspan=2, sticky="ew"
        )
        ttk.Label(frame, textvariable=self.status_var).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        ttk.Label(frame, text="surange:").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        self.surange_text = tk.Text(frame, height=5, width=70, state="disabled")
        self.surange_text.grid(row=6, column=0, columnspan=2, sticky="nsew")
        frame.rowconfigure(6, weight=1)

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a Seismic Unix file",
            filetypes=[("Seismic Unix files", "*.su"), ("All files", "*.*")],
        )
        if path:
            self.file_var.set(path)
            self.status_var.set("Ready to display.")
            self.inspect(path)

    def inspect(self, path: Optional[Path] = None) -> None:
        path = Path(path or self.file_var.get()).expanduser()
        if not path.is_file():
            self._set_surange("File not found.")
            return
        if shutil.which("surange") is None:
            self._set_surange("surange not found on PATH.")
            return
        try:
            result = subprocess.run(
                ["surange"],
                input=path.read_bytes(),
                capture_output=True,
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            self._set_surange(f"Could not run surange: {error}")
            return
        output = (result.stdout + result.stderr).decode(errors="replace").strip()
        self._set_surange(output or f"surange exited with status {result.returncode}.")

    def _set_surange(self, text: str) -> None:
        if self.surange_text is None:
            return
        self.surange_text.configure(state="normal")
        self.surange_text.delete("1.0", tk.END)
        self.surange_text.insert("1.0", text)
        self.surange_text.configure(state="disabled")

    def _get_perc(self) -> Optional[str]:
        try:
            perc = float(self.perc_var.get())
        except ValueError:
            messagebox.showerror(
                "Invalid percentile",
                "Enter a number greater than 0 and no greater than 100.",
            )
            return None
        if not math.isfinite(perc) or not 0 < perc <= 100:
            messagebox.showerror(
                "Invalid percentile",
                "Enter a number greater than 0 and no greater than 100.",
            )
            return None
        return f"{perc:g}"

    def display(self) -> None:
        path = Path(self.file_var.get()).expanduser()
        if not path.is_file():
            messagebox.showerror("File not found", f"Could not find:\n{path}")
            return
        perc = self._get_perc()
        if perc is None:
            return
        self.inspect(path)
        if shutil.which("suximage") is None:
            messagebox.showerror(
                "suximage not found",
                "Install Seismic Unix and make sure 'suximage' is on PATH.",
            )
            return
        if self.process and self.process.poll() is None:
            messagebox.showinfo("Viewer running", "Close the current suximage window first.")
            return

        try:
            self.input_file = path.open("rb")
            self.process = subprocess.Popen(
                ["suximage", f"perc={perc}"],
                stdin=self.input_file,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            self._close_input()
            messagebox.showerror("Could not start suximage", str(error))
            return

        self.status_var.set(f"Displaying {path.name} with suximage.")
        self.root.after(250, self._check_process)

    def _check_process(self) -> None:
        if self.process is None or self.process.poll() is None:
            self.root.after(250, self._check_process)
            return
        return_code = self.process.returncode
        self._close_input()
        self.process = None
        if return_code:
            self.status_var.set(f"suximage exited with status {return_code}.")
        else:
            self.status_var.set("suximage closed.")

    def _close_input(self) -> None:
        if self.input_file is not None:
            self.input_file.close()
            self.input_file = None

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self._close_input()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    SUImageViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()

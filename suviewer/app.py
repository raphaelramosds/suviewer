"""Select a Seismic Unix file and display it with ``suximage``."""

from __future__ import annotations

import math
import shutil
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import BinaryIO, Optional


class SUImageViewer:
    """Small Tkinter front end for the Seismic Unix ``suximage`` command."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.processes: dict[Path, subprocess.Popen[bytes]] = {}
        self.input_files: dict[Path, BinaryIO] = {}
        self.selected_files: list[Path] = []
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
        ttk.Button(frame, text="Add files...", command=self.choose_file).grid(
            row=1, column=1, sticky="ew", pady=(4, 12)
        )
        self.file_list = tk.Listbox(frame, height=5, selectmode=tk.EXTENDED)
        self.file_list.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 8))
        self.file_list.bind("<<ListboxSelect>>", self._select_file)
        file_buttons = ttk.Frame(frame)
        file_buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        file_buttons.columnconfigure(0, weight=1)
        file_buttons.columnconfigure(1, weight=1)
        ttk.Button(
            file_buttons, text="Remove selected", command=self.remove_selected
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(file_buttons, text="Clear files", command=self.clear_files).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        ttk.Label(frame, text="Amplitude percentile (perc):").grid(
            row=4, column=0, sticky="w", pady=(0, 12)
        )
        ttk.Spinbox(
            frame,
            from_=0.01,
            to=100,
            increment=0.5,
            textvariable=self.perc_var,
            width=10,
        ).grid(row=4, column=1, sticky="w", pady=(0, 12))
        action_buttons = ttk.Frame(frame)
        action_buttons.grid(row=5, column=0, columnspan=2, sticky="ew")
        action_buttons.columnconfigure(0, weight=1)
        action_buttons.columnconfigure(1, weight=1)
        ttk.Button(
            action_buttons, text="Display with suximage", command=self.display
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(
            action_buttons, text="Close all images", command=self.close_all_images
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(frame, textvariable=self.status_var).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        ttk.Label(frame, text="surange:").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        self.surange_text = tk.Text(frame, height=5, width=70, state="disabled")
        self.surange_text.grid(row=8, column=0, columnspan=2, sticky="nsew")
        frame.rowconfigure(2, weight=1)
        frame.rowconfigure(8, weight=1)

    def choose_file(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select Seismic Unix files",
            filetypes=[("Seismic Unix files", "*.su"), ("All files", "*.*")],
        )
        if paths:
            for path_string in paths:
                path = Path(path_string)
                if path not in self.selected_files:
                    self.selected_files.append(path)
                    self.file_list.insert(tk.END, str(path))
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(tk.END)
            self.file_list.see(tk.END)
            self.file_var.set(str(self.selected_files[-1]))
            self.status_var.set("Ready to display.")
            self.inspect()

    def _select_file(self, _event: tk.Event[tk.Listbox]) -> None:
        selection = self.file_list.curselection()
        if selection:
            self.file_var.set(self.file_list.get(selection[-1]))
            self.inspect()

    def remove_selected(self) -> None:
        indexes = list(self.file_list.curselection())
        for index in reversed(indexes):
            self.file_list.delete(index)
            del self.selected_files[index]
        if self.selected_files:
            self.file_var.set(str(self.selected_files[-1]))
            self.inspect()
        else:
            self.file_var.set("")
            self._set_surange("")

    def clear_files(self) -> None:
        self.file_list.delete(0, tk.END)
        self.selected_files.clear()
        self.file_var.set("")
        self._set_surange("")
        self.status_var.set("Select .su files to display.")

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
        paths = self.selected_files or [Path(self.file_var.get()).expanduser()]
        missing = [path for path in paths if not path.is_file()]
        if missing:
            messagebox.showerror(
                "File not found",
                "Could not find:\n" + "\n".join(str(path) for path in missing),
            )
            return
        perc = self._get_perc()
        if perc is None:
            return
        if shutil.which("suximage") is None:
            messagebox.showerror(
                "suximage not found",
                "Install Seismic Unix and make sure 'suximage' is on PATH.",
            )
            return

        started = 0
        for path in paths:
            if path in self.processes and self.processes[path].poll() is None:
                continue
            if path in self.processes:
                self._close_input(path)
                del self.processes[path]
            input_file: Optional[BinaryIO] = None
            try:
                input_file = path.open("rb")
                process = subprocess.Popen(
                    ["suximage", f"perc={perc}"],
                    stdin=input_file,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError as error:
                if input_file is not None:
                    input_file.close()
                messagebox.showerror(
                    "Could not start suximage", f"{path.name}: {error}"
                )
                continue
            if input_file is None:
                continue
            self.input_files[path] = input_file
            self.processes[path] = process
            started += 1

        if started:
            self.status_var.set(f"Displaying {started} file(s) with suximage.")
            self.root.after(250, self._check_process)
        elif paths:
            messagebox.showinfo("Viewer running", "The selected files are already open.")

    def _check_process(self) -> None:
        finished = [
            path for path, process in self.processes.items() if process.poll() is not None
        ]
        for path in finished:
            return_code = self.processes[path].returncode
            self._close_input(path)
            del self.processes[path]
            if return_code:
                self.status_var.set(
                    f"{path.name}: suximage exited with status {return_code}."
                )
        if self.processes:
            self.root.after(250, self._check_process)
        elif finished:
            self.status_var.set("All suximage windows closed.")

    def _close_input(self, path: Path) -> None:
        input_file = self.input_files.pop(path, None)
        if input_file is not None:
            input_file.close()

    def close_all_images(self) -> None:
        if not self.processes:
            self.status_var.set("No suximage windows are open.")
            return
        for process in self.processes.values():
            if process.poll() is None:
                process.terminate()
        for path in list(self.input_files):
            self._close_input(path)
        self.processes.clear()
        self.status_var.set("All suximage windows closed.")

    def close(self) -> None:
        for path, process in self.processes.items():
            if process.poll() is None:
                process.terminate()
            self._close_input(path)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    SUImageViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()

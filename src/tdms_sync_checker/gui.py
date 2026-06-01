from __future__ import annotations

from pathlib import Path
import traceback
import threading
import queue
import os
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import run_analysis, build_report_preview_text


class GeneralTDMSSyncCheckerGUI(tk.Tk):
    """Tkinter GUI for the metadata-first TDMS checker."""

    def __init__(self):
        super().__init__()

        self.title("General TDMS Synchronisation Checker - No Plots")
        self.geometry("1100x720")

        self.input_path_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()

        self.msg_queue = queue.Queue()
        self.worker_thread = None
        self.last_html_report = None
        self.last_output_folder = None

        self._build_gui()
        self.after(200, self.process_log_queue)

    def _build_gui(self):
        pad = {"padx": 8, "pady": 4}

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="General TDMS Synchronisation Checker",
            font=("Segoe UI", 16, "bold")
        )
        title.grid(row=0, column=0, columnspan=4, sticky="w", **pad)

        subtitle = ttk.Label(
            main,
            text="Metadata-first checker. No plots are created during the GUI run to avoid freezes with large TDMS files."
        )
        subtitle.grid(row=1, column=0, columnspan=4, sticky="w", **pad)

        ttk.Label(main, text="TDMS file/folder:").grid(row=2, column=0, sticky="w", **pad)

        ttk.Entry(
            main,
            textvariable=self.input_path_var,
            width=100
        ).grid(row=2, column=1, sticky="ew", **pad)

        ttk.Button(
            main,
            text="Browse TDMS File",
            command=self.browse_file
        ).grid(row=2, column=2, sticky="ew", **pad)

        ttk.Button(
            main,
            text="Browse TDMS Folder",
            command=self.browse_folder
        ).grid(row=2, column=3, sticky="ew", **pad)

        ttk.Label(main, text="Output folder:").grid(row=3, column=0, sticky="w", **pad)

        ttk.Entry(
            main,
            textvariable=self.output_folder_var,
            width=100
        ).grid(row=3, column=1, sticky="ew", **pad)

        ttk.Button(
            main,
            text="Browse Output Folder",
            command=self.browse_output
        ).grid(row=3, column=2, columnspan=2, sticky="ew", **pad)

        self.run_button = ttk.Button(
            main,
            text="Run General Analysis",
            command=self.run_analysis_threaded
        )
        self.run_button.grid(row=4, column=1, sticky="w", **pad)

        self.progress = ttk.Progressbar(
            main,
            mode="indeterminate"
        )
        self.progress.grid(row=5, column=0, columnspan=4, sticky="ew", **pad)

        notebook = ttk.Notebook(main)
        notebook.grid(row=6, column=0, columnspan=4, sticky="nsew", **pad)

        self.summary_text = tk.Text(notebook, height=25, wrap="word")
        self.report_text = tk.Text(notebook, height=25, wrap="none")
        self.log_text = tk.Text(notebook, height=25, wrap="word")

        notebook.add(self.summary_text, text="Results summary")
        notebook.add(self.report_text, text="Report preview")
        notebook.add(self.log_text, text="Log")

        button_frame = ttk.Frame(main)
        button_frame.grid(row=7, column=0, columnspan=4, sticky="ew", **pad)

        ttk.Button(
            button_frame,
            text="Open HTML report in browser",
            command=self.open_html_report
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Open output folder",
            command=self.open_output_folder
        ).pack(side="left", padx=4)

        main.columnconfigure(1, weight=1)
        main.rowconfigure(6, weight=1)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select TDMS file",
            filetypes=[
                ("TDMS files", "*.tdms"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.input_path_var.set(file_path)

            if not self.output_folder_var.get():
                self.output_folder_var.set(
                    str(Path(file_path).parent / "tdms_general_sync_outputs")
                )

    def browse_folder(self):
        folder_path = filedialog.askdirectory(
            title="Select folder containing TDMS files"
        )

        if folder_path:
            self.input_path_var.set(folder_path)

            if not self.output_folder_var.get():
                self.output_folder_var.set(
                    str(Path(folder_path) / "tdms_general_sync_outputs")
                )

    def browse_output(self):
        folder_path = filedialog.askdirectory(
            title="Select output folder"
        )

        if folder_path:
            self.output_folder_var.set(folder_path)

    def log(self, message):
        self.msg_queue.put(("log", str(message)))

    def set_summary(self, message):
        self.msg_queue.put(("summary", str(message)))

    def set_report_preview(self, message):
        self.msg_queue.put(("report", str(message)))

    def open_html_report(self):
        if self.last_html_report and Path(self.last_html_report).exists():
            webbrowser.open(Path(self.last_html_report).resolve().as_uri())
        else:
            messagebox.showinfo("No report yet", "Run the analysis first.")

    def open_output_folder(self):
        if self.last_output_folder and Path(self.last_output_folder).exists():
            path = Path(self.last_output_folder)
            if os.name == "nt":
                os.startfile(path)
            else:
                webbrowser.open(path.resolve().as_uri())
        else:
            messagebox.showinfo("No output folder yet", "Run the analysis first.")

    def run_analysis_threaded(self):
        if self.worker_thread is not None and self.worker_thread.is_alive():
            messagebox.showwarning("Busy", "Analysis is already running.")
            return

        self.log_text.delete("1.0", "end")
        self.summary_text.delete("1.0", "end")
        self.report_text.delete("1.0", "end")
        self.progress.start()
        self.run_button.config(state="disabled")

        self.worker_thread = threading.Thread(
            target=self.run_analysis_safe,
            daemon=True
        )
        self.worker_thread.start()

    def run_analysis_safe(self):
        try:
            input_path_text = self.input_path_var.get().strip()
            output_folder_text = self.output_folder_var.get().strip()

            if not input_path_text:
                raise ValueError("Please select a TDMS file or folder.")

            if not output_folder_text:
                raise ValueError("Please select an output folder.")

            input_path = Path(input_path_text)
            output_folder = Path(output_folder_text)

            if not input_path.exists():
                raise FileNotFoundError(f"Input path does not exist:\n{input_path}")

            self.log(f"Input: {input_path}")
            self.log(f"Output: {output_folder}")

            result, excel_path, html_path, summary_text = run_analysis(
                input_path,
                output_folder,
                log_func=self.log
            )

            report_preview_text = build_report_preview_text(result, summary_text)
            self.set_summary(summary_text)
            self.set_report_preview(report_preview_text)
            self.msg_queue.put(("done", (str(html_path), str(excel_path), str(output_folder))))

        except Exception as exc:
            error_text = traceback.format_exc()
            self.log("")
            self.log("ERROR:")
            self.log(error_text)
            self.msg_queue.put(("error", str(exc)))

        finally:
            self.msg_queue.put(("enable", ""))

    def process_log_queue(self):
        try:
            while True:
                msg_type, msg = self.msg_queue.get_nowait()

                if msg_type == "log":
                    self.log_text.insert("end", msg + "\n")
                    self.log_text.see("end")

                elif msg_type == "summary":
                    self.summary_text.delete("1.0", "end")
                    self.summary_text.insert("end", msg)
                    self.summary_text.see("1.0")

                elif msg_type == "report":
                    self.report_text.delete("1.0", "end")
                    self.report_text.insert("end", msg)
                    self.report_text.see("1.0")

                elif msg_type == "done":
                    html_path, excel_path, output_folder = msg
                    self.last_html_report = html_path
                    self.last_output_folder = output_folder
                    messagebox.showinfo(
                        "Analysis complete",
                        f"General TDMS analysis complete.\n\n"
                        f"HTML report:\n{html_path}\n\n"
                        f"Excel report:\n{excel_path}"
                    )

                elif msg_type == "error":
                    messagebox.showerror("Error", msg)

                elif msg_type == "enable":
                    self.progress.stop()
                    self.run_button.config(state="normal")

        except queue.Empty:
            pass

        self.after(200, self.process_log_queue)


def main():
    app = GeneralTDMSSyncCheckerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

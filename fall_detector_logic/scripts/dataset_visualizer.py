import os
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class DatasetVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("CSI Dataset Visualizer")
        self.geometry("1400x850")

        self.current_folder = ""
        self.csv_files = []
        self.df = None
        self.subcarrier_data = None
        
        # UI State
        self.view_mode = tk.StringVar(value="heatmap") # "heatmap", "lines_all", "line_single"
        self.selected_subcarrier = tk.IntVar(value=0)

        self._build_ui()
        self._auto_load_default_folder()
        
    def _auto_load_default_folder(self):
        # Try to find 'data/raw' relative to the project root
        possible_paths = [
            'D:\\Projects\\major\\project_v3\\data\\raw\\empty',
            os.path.join(os.getcwd(), "data", "raw"),
            os.path.join(os.getcwd(), "project_v3", "data", "raw"),
            os.path.join(os.path.dirname(__file__), "..", "data", "raw")
        ]
        
        for p in possible_paths:
            if os.path.exists(p):
                self._load_folder(os.path.abspath(p))
                return

    def _build_ui(self):
        # Top Control Bar
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(top_frame, text="Open Folder", command=self._open_folder).pack(side=tk.LEFT, padx=5)
        self.lbl_folder = ttk.Label(top_frame, text="No folder selected", foreground="grey")
        self.lbl_folder.pack(side=tk.LEFT, padx=5)

        # Main Content Area
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Sidebar: File List
        sidebar = ttk.Frame(main_paned)
        main_paned.add(sidebar, weight=1)

        ttk.Label(sidebar, text="Datasets (.csv)", font=("Arial", 10, "bold")).pack(pady=5)
        self.file_listbox = tk.Listbox(sidebar, selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self._on_file_select)

        # Right Area: Visualization
        viz_frame = ttk.Frame(main_paned)
        main_paned.add(viz_frame, weight=4)
        
        # Configure viz_frame grid for stable layout
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(1, weight=1)

        # Viz Controls
        controls = ttk.LabelFrame(viz_frame, text="Visualization Controls")
        controls.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(controls, text="View Mode:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(controls, text="Mode 1: Heatmap", variable=self.view_mode, value="heatmap", command=self._update_plot).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(controls, text="Mode 2: All Lines Overlay", variable=self.view_mode, value="lines_all", command=self._update_plot).grid(row=0, column=2, padx=5)
        ttk.Radiobutton(controls, text="Mode 3: Individual Line", variable=self.view_mode, value="line_single", command=self._update_plot).grid(row=0, column=3, padx=5)

        ttk.Label(controls, text="Subcarrier:").grid(row=0, column=4, padx=10)
        self.subcarrier_combo = ttk.Combobox(controls, values=[f"SC {i}" for i in range(52)], width=8, state="disabled")
        self.subcarrier_combo.grid(row=0, column=5, padx=5)
        self.subcarrier_combo.bind("<<ComboboxSelected>>", self._on_subcarrier_change)
        self.subcarrier_combo.set("SC 0")

        # Plotting Area
        self.fig, self.ax = plt.subplots(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
        
        self.toolbar_frame = ttk.Frame(viz_frame)
        self.toolbar_frame.grid(row=2, column=0, sticky="ew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

    def _open_folder(self):
        default_dir = os.path.join(os.getcwd(), "data", "raw")
        if not os.path.exists(default_dir):
            default_dir = os.getcwd()
            
        folder = filedialog.askdirectory(initialdir=default_dir)
        if folder:
            self._load_folder(folder)

    def _load_folder(self, folder):
        self.current_folder = folder
        self.lbl_folder.config(text=folder)
        
        try:
            self.csv_files = [f for f in os.listdir(folder) if f.endswith(".csv")]
            self.file_listbox.delete(0, tk.END)
            for f in self.csv_files:
                self.file_listbox.insert(tk.END, f)
        except Exception as e:
            messagebox.showerror("Error", f"Could not list directory: {e}")

    def _on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return

        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.current_folder, filename)
        
        try:
            self.df = pd.read_csv(filepath)
            # Assuming subcarriers are the last 52 columns
            self.subcarrier_data = self.df.iloc[:, -52:].values
            self._update_plot()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load CSV: {e}")

    def _on_subcarrier_change(self, event):
        idx = self.subcarrier_combo.current()
        if idx >= 0:
            self.selected_subcarrier.set(idx)
            self._update_plot()

    def _update_plot(self):
        self.ax.clear()
        
        if self.subcarrier_data is None:
            self.ax.text(0.5, 0.5, "Please select a dataset file from the sidebar", 
                        ha="center", va="center", transform=self.ax.transAxes)
            self.canvas.draw()
            return

        mode = self.view_mode.get()
        
        if mode == "heatmap":
            self.subcarrier_combo.config(state="disabled")
            im = self.ax.imshow(self.subcarrier_data.T, aspect='auto', cmap='viridis', interpolation='nearest')
            self.ax.set_title("Spectral Signature Heatmap (Packet Index vs Subcarrier Index)")
            self.ax.set_xlabel("Packet Index")
            self.ax.set_ylabel("Subcarrier Index")
        elif mode == "lines_all":
            self.subcarrier_combo.config(state="disabled")
            self.ax.plot(self.subcarrier_data, alpha=0.3, linewidth=0.5)
            self.ax.set_title("All Subcarriers Overlay (Packet Index vs Amplitude)")
            self.ax.set_xlabel("Packet Index")
            self.ax.set_ylabel("Amplitude")
            self.ax.grid(True, alpha=0.3)
        else: # line_single
            self.subcarrier_combo.config(state="readonly")
            sc_idx = self.selected_subcarrier.get()
            self.ax.plot(self.subcarrier_data[:, sc_idx], color='blue', linewidth=1)
            self.ax.set_title(f"Subcarrier {sc_idx} Amplitude (Packet Index vs Amplitude)")
            self.ax.set_xlabel("Packet Index")
            self.ax.set_ylabel("Amplitude")
            self.ax.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    app = DatasetVisualizer()
    app.mainloop()

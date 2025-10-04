import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sympy as sp
import os
import csv
import pandas as pd

# Helper for color name conversion (uses basic mapping; you can extend as needed)
def hex_to_name(hex_color):
    web_colors = {
        '#000000': 'black', '#ffffff': 'white', '#ff0000': 'red', '#008000': 'green', 
        '#0000ff': 'blue', '#ffff00': 'yellow', '#00ffff': 'cyan', '#ff00ff': 'magenta',
        '#800000': 'maroon', '#808000': 'olive', '#800080': 'purple', '#008080': 'teal',
        '#c0c0c0': 'silver', '#808080': 'gray', '#f0e68c': 'khaki', '#6a11cb': 'custom' # Example fallback
    }
    hex_color = hex_color.lower()
    if hex_color in web_colors:
        return web_colors[hex_color]
    # Fallback: show 'custom' or the hex code itself
    return 'custom' if not hex_color in web_colors else web_colors[hex_color]

class EquationGrapherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨📈 Fancy Equation Grapher")
        self.history = []
        self.history_csv_path = 'equation_history.csv'
        self.create_styles()
        self.create_widgets()
        self.load_history_csv()
        self.update_history_list()
        self.load_example("x^2")
        self._drag_start_x = None
        self._drag_start_y = None

    def create_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#14213d")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 11), foreground="#444")
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=6)
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        self.style.map("Accent.TButton", background=[('active', '#ffb86b'), ('!active', '#ff8c42')])
        self.style.configure("TEntry", padding=6, font=("Courier New", 12))
        self.style.configure("Panel.TFrame", background="#f8fbff")
        self.style.configure("Graph.TFrame", background="#0f1724")
        self.style.configure("History.TFrame", background="#fffaf0")

    def create_widgets(self):
        self.root.configure(bg="#f8fbff")
        header_canvas = tk.Canvas(self.root, height=80, highlightthickness=0, bg="#ff8c42")  # Match gradient start
        header_canvas.pack(fill="x", padx=0, pady=(10, 6))
        width = self.root.winfo_screenwidth()
        self._draw_gradient_header(header_canvas, "#ff8c42", "#6a11cb", "#2575fc")
        header_canvas.create_text(header_canvas.winfo_reqwidth()//2 if header_canvas.winfo_reqwidth() > 0 else 600, 40,
                                 text="🎨 Equation Grapher", anchor="center",
                                 font=("Segoe UI", 20, "bold"), fill="white")
        header_canvas.create_text(header_canvas.winfo_reqwidth()//2 if header_canvas.winfo_reqwidth() > 0 else 600, 65,
                                 text="Visualise functions • Save history", anchor="center",
                                 font=("Segoe UI", 11), fill="white")

        self.main_frame = ttk.Frame(self.root, style="Panel.TFrame", padding=12)
        self.main_frame.pack(fill="both", expand=True, padx=12, pady=(6,12))
        self.control_frame = ttk.Frame(self.main_frame, style="Panel.TFrame", padding=10)
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=(0,12))
        self.plot_frame = ttk.Frame(self.main_frame, style="Graph.TFrame", padding=8)
        self.plot_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        # Input Widgets
        title = ttk.Label(self.control_frame, text="🔢 Enter Equation", style="Header.TLabel")
        title.pack(anchor="center", pady=(0,8))  # ** Centered **
        self.equation_var = tk.StringVar()
        self.equation_entry = ttk.Entry(self.control_frame, textvariable=self.equation_var, width=28, style="TEntry")
        self.equation_entry.pack(fill="x", pady=(0,10))
        self.equation_entry.bind("<Return>", lambda e: self.plot_equation())

        range_frame = ttk.Frame(self.control_frame)
        range_frame.pack(fill="x", pady=(6,10))
        ttk.Label(range_frame, text="Min X").grid(row=0, column=0, sticky="w")
        ttk.Label(range_frame, text="Max X").grid(row=0, column=1, sticky="w", padx=(8,0))
        self.min_x_var = tk.StringVar(value="-10")
        self.max_x_var = tk.StringVar(value="10")
        self.min_x_entry = ttk.Entry(range_frame, textvariable=self.min_x_var, width=12, style="TEntry")
        self.min_x_entry.grid(row=1, column=0, sticky="w")
        self.max_x_entry = ttk.Entry(range_frame, textvariable=self.max_x_var, width=12, style="TEntry")
        self.max_x_entry.grid(row=1, column=1, sticky="w", padx=(8,0))

        color_frame = ttk.Frame(self.control_frame)
        color_frame.pack(fill="x", pady=(12,10))
        ttk.Label(color_frame, text="Line color:").grid(row=0, column=0, sticky="w")
        self.line_color_var = tk.StringVar(value="#6a11cb")
        self.color_preview = tk.Canvas(color_frame, width=40, height=22, bg=self.line_color_var.get(), highlightthickness=1)
        self.color_preview.grid(row=1, column=1, padx=(8,6), sticky="w")
        self.color_button = ttk.Button(color_frame, text="Pick", command=self.pick_color, style="Accent.TButton")
        self.color_button.grid(row=1, column=2, sticky="w")

        self.plot_button = ttk.Button(self.control_frame, text="📈 Plot Graph", command=self.plot_equation, style="Primary.TButton")
        self.plot_button.pack(fill="x", pady=(8,6))

        theme_frame = ttk.Frame(self.control_frame)
        theme_frame.pack(fill="x", pady=(12,6))
        ttk.Label(theme_frame, text="Theme:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.theme_var = tk.StringVar(value="dark")
        dark_rb = ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, value="dark", command=self.apply_theme)
        light_rb = ttk.Radiobutton(theme_frame, text="Light", variable=self.theme_var, value="light", command=self.apply_theme)
        dark_rb.grid(row=0, column=1, padx=6)
        light_rb.grid(row=0, column=2, padx=6)

        ttk.Label(self.control_frame, text="💡 Examples:", style="SubHeader.TLabel").pack(anchor="center", pady=(10,6))
        examples = ["x^2", "sin(x)", "cos(x)", "tan(x)", "exp(x)", "log(x)", "abs(x)", "sqrt(x)"]
        eg_frame = ttk.Frame(self.control_frame)
        eg_frame.pack(fill="x")
        for eq in examples:
            b = ttk.Button(eg_frame, text=eq, width=8, command=lambda e=eq: self.load_example(e), style="Accent.TButton")
            b.pack(side="left", padx=4, pady=4)

        hist_title = ttk.Label(self.control_frame, text="📚 History", style="Header.TLabel")
        hist_title.pack(anchor="center", pady=(12,6))  # ** Centered **
        self.history_frame = ttk.Frame(self.control_frame, style="History.TFrame", padding=6)
        self.history_frame.pack(fill="both", expand=True)
        self.history_listbox = tk.Listbox(self.history_frame, height=8, font=("Courier New", 11), bg="#fffaf0")
        self.history_listbox.pack(side="left", fill="both", expand=True)
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)
        scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.history_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        hist_btns = ttk.Frame(self.control_frame)
        hist_btns.pack(fill="x", pady=(8,0))
        ttk.Button(hist_btns, text="Delete", command=self.delete_selected_history, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(hist_btns, text="Clear All", command=self.clear_history, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(hist_btns, text="Save Excel", command=self.save_history_to_excel, style="Primary.TButton").pack(side="left", padx=4)

        self.message_var = tk.StringVar()
        self.message_label = ttk.Label(self.control_frame, textvariable=self.message_var, font=("Segoe UI", 10, "italic"))
        self.message_label.pack(pady=(8,2))

        self.create_graph_panel()

    def _draw_gradient_header(self, canvas, *colors):
        canvas_width = max(canvas.winfo_reqwidth(), 1200)
        steps = 200
        w = canvas_width / steps
        for i in range(steps):
            t = i / (steps - 1)
            if t < 0.5:
                a = t * 2
                c1 = self._hex_to_rgb(colors[0])
                c2 = self._hex_to_rgb(colors[1])
                rgb = self._interp_rgb(c1, c2, a)
            else:
                a = (t - 0.5) * 2
                c2 = self._hex_to_rgb(colors[1])
                c3 = self._hex_to_rgb(colors[2])
                rgb = self._interp_rgb(c2, c3, a)
            hexc = self._rgb_to_hex(rgb)
            canvas.create_rectangle(i*w, 0, (i+1)*w, 80, outline=hexc, fill=hexc)

    def _hex_to_rgb(self, h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    def _rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))
    def _interp_rgb(self, a, b, t):
        return (a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t, a[2] + (b[2]-a[2])*t)

    def create_graph_panel(self):
        self.fig, self.ax = plt.subplots(figsize=(7,5))
        self.apply_plot_style(dark=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)
        overlay = tk.Frame(self.plot_frame, bg="", bd=0)
        overlay.place(relx=0.01, rely=0.01, anchor="nw")
        ttk.Button(overlay, text="🗑 Clear", command=self.clear_graph, style="Accent.TButton").pack(side="left", padx=6)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_button_press)
        self.canvas.mpl_connect("button_release_event", self.on_button_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

    def apply_plot_style(self, dark=True):
        if dark:
            self.fig.patch.set_facecolor('#0f1724')
            self.ax.set_facecolor('#071428')
            tick_color = 'white'
            spine_color = 'white'
            title_color = 'white'
            grid_col = '#1f2a44'
        else:
            self.fig.patch.set_facecolor('#ffffff')
            self.ax.set_facecolor('#f7fbff')
            tick_color = '#222222'
            spine_color = '#222222'
            title_color = '#14213d'
            grid_col = '#e6e9ef'
        self.ax.clear()
        self.ax.tick_params(colors=tick_color)
        for side in ['bottom','top','left','right']:
            self.ax.spines[side].set_color(spine_color)
        self.ax.xaxis.label.set_color(tick_color)
        self.ax.yaxis.label.set_color(tick_color)
        self.ax.title.set_color(title_color)
        self.ax.grid(True, color=grid_col)

    def apply_theme(self):
        theme = self.theme_var.get()
        if theme == "dark":
            self.apply_plot_style(dark=True)
        else:
            self.apply_plot_style(dark=False)
        self.canvas.draw_idle()
        self.show_message(f"Applied {theme} theme")

    def pick_color(self):
        color_code = colorchooser.askcolor(title="Choose Line Color", initialcolor=self.line_color_var.get())
        if color_code[1]:
            self.line_color_var.set(color_code[1])
            self.color_preview.config(bg=color_code[1])

    def plot_equation(self):
        equation = self.equation_var.get().strip()
        if not equation:
            self.show_message("Please enter an equation", error=True)
            return
        try:
            min_x = float(self.min_x_var.get())
            max_x = float(self.max_x_var.get())
        except ValueError:
            self.show_message("Min X and Max X must be valid numbers", error=True)
            return
        if min_x >= max_x:
            self.show_message("Min X must be less than Max X", error=True)
            return
        eq_for_sympy = equation.replace('^', '**')
        x = sp.symbols('x')
        try:
            expr = sp.sympify(eq_for_sympy)
        except (sp.SympifyError, TypeError):
            self.show_message("Invalid mathematical expression", error=True)
            return
        x_vals = np.linspace(min_x, max_x, 1200)
        f = sp.lambdify(x, expr, modules=["numpy"])
        try:
            y_vals = f(x_vals)
        except Exception as e:
            self.show_message(f"Error evaluating function: {e}", error=True)
            return
        y_vals = np.array(y_vals, dtype=np.complex128)
        real_mask = np.isfinite(y_vals.real)
        imag_mask = y_vals.imag == 0
        mask = real_mask & imag_mask
        if not np.any(mask):
            self.show_message("Function has no valid real outputs in this range", error=True)
            return
        color = self.line_color_var.get()
        colorname = hex_to_name(color)  # Color name conversion
        self.ax.plot(x_vals[mask], y_vals.real[mask], color=color, linewidth=2.2, label=equation)
        self.ax.legend(loc="upper left", facecolor="#ffffff", framealpha=0.85, edgecolor=color, fontsize=10)
        self.ax.set_title('Mathematical Function Graph', loc='center')
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('f(x)')
        self.canvas.draw_idle()
        if not self.history or (self.history and self.history[-1]["equation"] != equation):
            self.history.append({"equation": equation, "min_x": min_x, "max_x": max_x, "color": color,
                                 "colorname": colorname, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            self.update_history_list()
            self.save_history_csv()
        self.show_message(f"Plotted: {equation}")

    def clear_graph(self):
        self.apply_plot_style(dark=(self.theme_var.get()=="dark"))
        self.ax.clear()
        self.apply_plot_style(dark=(self.theme_var.get()=="dark"))
        self.ax.set_title('Mathematical Function Graph', loc='center')
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('f(x)')
        self.canvas.draw_idle()
        self.show_message("Graph cleared")

    def update_history_list(self):
        self.history_listbox.delete(0, tk.END)
        for item in self.history:
            display = f"{item['equation']}  |  [{item['min_x']}, {item['max_x']}]  •  {item['timestamp']}"
            self.history_listbox.insert(tk.END, display)

    def on_history_select(self, event):
        sel = event.widget.curselection()
        if not sel:
            return
        idx = sel[0]
        item = self.history[idx]
        self.equation_var.set(item["equation"])
        self.min_x_var.set(str(item["min_x"]))
        self.max_x_var.set(str(item["max_x"]))
        self.line_color_var.set(item["color"])
        self.color_preview.config(bg=item["color"])
        self.show_message("Loaded equation from history")

    def delete_selected_history(self):
        selection = self.history_listbox.curselection()
        if not selection:
            self.show_message("No history selected to delete", error=True)
            return
        idx = selection[0]
        del self.history[idx]
        self.update_history_list()
        self.save_history_csv()
        self.show_message("Deleted selected history")

    def clear_history(self):
        if messagebox.askyesno("Confirm Clear", "Clear all equation history?"):
            self.history.clear()
            self.update_history_list()
            self.save_history_csv()
            self.show_message("Cleared all history")

    def save_history_csv(self):
        with open(self.history_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['equation', 'min_x', 'max_x', 'color', 'colorname', 'timestamp'])
            writer.writeheader()
            for item in self.history:
                writer.writerow({
                    'equation': item['equation'],
                    'min_x': item['min_x'],
                    'max_x': item['max_x'],
                    'color': item['color'],
                    'colorname': item['colorname'],
                    'timestamp': item['timestamp']
                })

    def load_history_csv(self):
        if not os.path.exists(self.history_csv_path):
            self.history = []
            return
        with open(self.history_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            self.history = [
                {
                    'equation': row['equation'],
                    'min_x': float(row['min_x']),
                    'max_x': float(row['max_x']),
                    'color': row['color'],
                    'colorname': row.get('colorname', hex_to_name(row['color'])),
                    'timestamp': row['timestamp']
                } for row in reader
            ]

    def save_history_to_excel(self):
        if not self.history:
            self.show_message('No history to save in Excel')
            return
        df = pd.DataFrame(self.history)
        df.to_excel('equation_history.xlsx', index=False)
        self.show_message('History saved to Excel (equation_history.xlsx)')

    def load_example(self, eq):
        self.equation_var.set(eq)
        self.show_message(f"Loaded example: {eq}")

    def show_message(self, msg, error=False):
        self.message_var.set(msg)
        self.message_label.config(foreground="#d32f2f" if error else "#2e7d32")

    def on_scroll(self, event):
        base_scale = 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None:
            return
        scale_factor = 1 / base_scale if event.button == 'up' else base_scale if event.button == 'down' else 1
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        self.canvas.draw_idle()

    def on_button_press(self, event):
        if event.button == 1 and event.inaxes:
            self._drag_start_x = event.x
            self._drag_start_y = event.y
            self._orig_xlim = self.ax.get_xlim()
            self._orig_ylim = self.ax.get_ylim()

    def on_button_release(self, event):
        self._drag_start_x = None
        self._drag_start_y = None

    def on_motion(self, event):
        if self._drag_start_x is None or self._drag_start_y is None or event.x is None or event.y is None or not event.inaxes:
            return
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        dx_data = dx * (self._orig_xlim[1] - self._orig_xlim[0]) / self.canvas.get_tk_widget().winfo_width()
        dy_data = dy * (self._orig_ylim[1] - self._orig_ylim[0]) / self.canvas.get_tk_widget().winfo_height()
        self.ax.set_xlim(self._orig_xlim[0] - dx_data, self._orig_xlim[1] - dx_data)
        self.ax.set_ylim(self._orig_ylim[0] + dy_data, self._orig_ylim[1] + dy_data)
        self.canvas.draw_idle()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x780")
    app = EquationGrapherApp(root)
    root.mainloop()

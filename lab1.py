import math
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser

class ColorConverter:
    
    Xw, Yw, Zw = 95.047, 100.0, 108.883
    
    @staticmethod
    def rgb_to_xyz(rgb):
        r, g, b = rgb
        
        def f(c):
            c = c / 255.0
            if c > 0.04045:
                return ((c + 0.055) / 1.055) ** 2.4
            else:
                return c / 12.92
        
        rn = f(r) * 100
        gn = f(g) * 100
        bn = f(b) * 100
        
        matrix = np.array([
            [0.412453, 0.357580, 0.180423],
            [0.212671, 0.715160, 0.072169],
            [0.019334, 0.119193, 0.950227]
        ])
        
        xyz = matrix @ np.array([rn, gn, bn])
        return xyz
    
    @staticmethod
    def xyz_to_rgb(xyz):
        x, y, z = xyz
        
        matrix = np.array([
            [3.2406, -1.5372, -0.4986],
            [-0.9689, 1.8758, 0.0415],
            [0.0557, -0.2040, 1.0570]
        ])
        
        rgbn = matrix @ np.array([x/100, y/100, z/100])
        
        def f_inv(c):
            if c > 0.0031308:
                return 1.055 * (c ** (1/2.4)) - 0.055
            else:
                return 12.92 * c
        
        rgb = [f_inv(c) * 255 for c in rgbn]
        rgb = [max(0, min(255, c)) for c in rgb]
        return rgb
    
    @staticmethod
    def xyz_to_lab(xyz):
        x, y, z = xyz
        
        def f(t):
            if t > 0.008856:
                return t ** (1/3)
            else:
                return 7.787 * t + 16/116
        
        fx = f(x / ColorConverter.Xw)
        fy = f(y / ColorConverter.Yw)
        fz = f(z / ColorConverter.Zw)
        
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return [L, a, b]
    
    @staticmethod
    def lab_to_xyz(lab):
        L, a, b = lab
        
        def f_inv(t):
            if t > 0.008856:
                return t ** 3
            else:
                return (t - 16/116) / 7.787
        
        fy = (L + 16) / 116
        fx = a / 500 + fy
        fz = fy - b / 200
        
        x = ColorConverter.Xw * f_inv(fx)
        y = ColorConverter.Yw * f_inv(fy)
        z = ColorConverter.Zw * f_inv(fz)
        
        return [x, y, z]

class ModernColorApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("RGB ↔ XYZ ↔ LAB")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2b2b2b')
        
        self.setup_styles()
        
        self.current_rgb = [128, 128, 128]
        self.updating = False
        self.clipping_warning_shown = False
        
        self.setup_ui()
        self.update_all_models()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=6)
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#4fc3f7')
        style.configure('Model.TLabelframe', background='#2b2b2b', foreground='white')
        style.configure('Model.TLabelframe.Label', background='#2b2b2b', foreground='#4fc3f7', font=('Segoe UI', 11, 'bold'))
        
        style.configure('Red.Horizontal.TScale', background='#2b2b2b')
        style.configure('Green.Horizontal.TScale', background='#2b2b2b')
        style.configure('Blue.Horizontal.TScale', background='#2b2b2b')
        
        style.configure('TEntry', font=('Segoe UI', 10))
    
    def setup_ui(self):
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        self.setup_color_preview(main_container)
        
        models_frame = ttk.Frame(main_container)
        models_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        models_frame.columnconfigure(0, weight=1)
        models_frame.columnconfigure(1, weight=1)
        models_frame.columnconfigure(2, weight=1)
        
        self.setup_rgb_section(models_frame, 0)
        self.setup_xyz_section(models_frame, 1)
        self.setup_lab_section(models_frame, 2)
        
        self.setup_control_panel(main_container)
        self.setup_status_bar(main_container)
    
    def setup_color_preview(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="Color Preview", style='Model.TLabelframe')
        preview_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.color_display = tk.Canvas(preview_frame, width=300, height=80, bg='#787878', 
                                     relief='flat', bd=0, highlightthickness=0)
        self.color_display.pack(pady=15, padx=20)
        
        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.hex_label = ttk.Label(info_frame, text="#808080", font=('Segoe UI', 12, 'bold'))
        self.hex_label.pack(side=tk.LEFT)
        
        self.rgb_label = ttk.Label(info_frame, text="RGB(128, 128, 128)", 
                                 font=('Segoe UI', 10), foreground='#bbbbbb')
        self.rgb_label.pack(side=tk.RIGHT)
    
    def setup_rgb_section(self, parent, column):
        frame = ttk.LabelFrame(parent, text="RGB Color Model", style='Model.TLabelframe')
        frame.grid(row=0, column=column, sticky='nsew', padx=10, pady=5)
        
        components = [
            ('R', 'Red', '#ff4444'),
            ('G', 'Green', '#44ff44'), 
            ('B', 'Blue', '#4444ff')
        ]
        
        self.rgb_entries = []
        self.rgb_sliders = []
        self.rgb_labels = []
        
        for i, (comp, name, color) in enumerate(components):
            comp_frame = ttk.Frame(frame)
            comp_frame.pack(fill=tk.X, padx=15, pady=8)
            
            label_frame = ttk.Frame(comp_frame)
            label_frame.pack(fill=tk.X)
            
            color_indicator = tk.Canvas(label_frame, width=16, height=16, bg=color, 
                                      relief='flat', bd=0, highlightthickness=1, highlightbackground='#555555')
            color_indicator.pack(side=tk.LEFT, padx=(0, 8))
            
            ttk.Label(label_frame, text=f"{name} ({comp})", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
            
            value_label = ttk.Label(label_frame, text="128", font=('Segoe UI', 10, 'bold'), foreground=color)
            value_label.pack(side=tk.RIGHT)
            self.rgb_labels.append(value_label)
            
            input_frame = ttk.Frame(comp_frame)
            input_frame.pack(fill=tk.X, pady=5)
            
            entry = ttk.Entry(input_frame, width=8, font=('Segoe UI', 10), justify='center')
            entry.pack(side=tk.LEFT, padx=(0, 10))
            entry.insert(0, "128")
            entry.bind('<KeyRelease>', lambda e, idx=i: self.on_rgb_entry_change(idx))
            self.rgb_entries.append(entry)
            
            slider = ttk.Scale(input_frame, from_=0, to=255, orient=tk.HORIZONTAL, 
                             length=180, style=f'{comp}.Horizontal.TScale')
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            slider.set(128)
            slider.bind('<B1-Motion>', lambda e, idx=i: self.on_rgb_slider_change(idx))
            slider.bind('<ButtonRelease-1>', lambda e, idx=i: self.on_rgb_slider_change(idx))
            self.rgb_sliders.append(slider)
    
    def setup_xyz_section(self, parent, column):
        frame = ttk.LabelFrame(parent, text="XYZ Color Model", style='Model.TLabelframe')
        frame.grid(row=0, column=column, sticky='nsew', padx=10, pady=5)
        
        components = [
            ('X', 'X Component', '#ffaa44'),
            ('Y', 'Y Component', '#aaff44'),
            ('Z', 'Z Component', '#44aaff')
        ]
        
        self.xyz_entries = []
        self.xyz_sliders = []
        self.xyz_labels = []
        
        for i, (comp, name, color) in enumerate(components):
            comp_frame = ttk.Frame(frame)
            comp_frame.pack(fill=tk.X, padx=15, pady=8)
            
            label_frame = ttk.Frame(comp_frame)
            label_frame.pack(fill=tk.X)
            
            color_indicator = tk.Canvas(label_frame, width=16, height=16, bg=color,
                                      relief='flat', bd=0, highlightthickness=1, highlightbackground='#555555')
            color_indicator.pack(side=tk.LEFT, padx=(0, 8))
            
            ttk.Label(label_frame, text=f"{name} ({comp})", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
            
            value_label = ttk.Label(label_frame, text="0.00", font=('Segoe UI', 10, 'bold'), foreground=color)
            value_label.pack(side=tk.RIGHT)
            self.xyz_labels.append(value_label)
            
            input_frame = ttk.Frame(comp_frame)
            input_frame.pack(fill=tk.X, pady=5)
            
            entry = ttk.Entry(input_frame, width=8, font=('Segoe UI', 10), justify='center')
            entry.pack(side=tk.LEFT, padx=(0, 10))
            entry.insert(0, "0.00")
            entry.bind('<KeyRelease>', lambda e, idx=i: self.on_xyz_entry_change(idx))
            self.xyz_entries.append(entry)
            
            slider = ttk.Scale(input_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                             length=180, style=f'{comp}.Horizontal.TScale')
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            slider.set(0)
            slider.bind('<B1-Motion>', lambda e, idx=i: self.on_xyz_slider_change(idx))
            slider.bind('<ButtonRelease-1>', lambda e, idx=i: self.on_xyz_slider_change(idx))
            self.xyz_sliders.append(slider)
    
    def setup_lab_section(self, parent, column):
        frame = ttk.LabelFrame(parent, text="LAB Color Model", style='Model.TLabelframe')
        frame.grid(row=0, column=column, sticky='nsew', padx=10, pady=5)
        
        components = [
            ('L', 'Lightness', '#ffffff'),
            ('A', 'A Axis', '#ff44ff'),
            ('B', 'B Axis', '#ffff44')
        ]
        
        self.lab_entries = []
        self.lab_sliders = []
        self.lab_labels = []
        
        for i, (comp, name, color) in enumerate(components):
            comp_frame = ttk.Frame(frame)
            comp_frame.pack(fill=tk.X, padx=15, pady=8)
            
            label_frame = ttk.Frame(comp_frame)
            label_frame.pack(fill=tk.X)
            
            color_indicator = tk.Canvas(label_frame, width=16, height=16, bg=color,
                                      relief='flat', bd=0, highlightthickness=1, highlightbackground='#555555')
            color_indicator.pack(side=tk.LEFT, padx=(0, 8))
            
            ttk.Label(label_frame, text=f"{name} ({comp})", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
            
            value_label = ttk.Label(label_frame, text="0.00", font=('Segoe UI', 10, 'bold'), foreground=color)
            value_label.pack(side=tk.RIGHT)
            self.lab_labels.append(value_label)
            
            input_frame = ttk.Frame(comp_frame)
            input_frame.pack(fill=tk.X, pady=5)
            
            entry = ttk.Entry(input_frame, width=8, font=('Segoe UI', 10), justify='center')
            entry.pack(side=tk.LEFT, padx=(0, 10))
            entry.insert(0, "0.00")
            entry.bind('<KeyRelease>', lambda e, idx=i: self.on_lab_entry_change(idx))
            self.lab_entries.append(entry)
            
            if comp == 'L':
                slider_range = (0, 100)
            else:
                slider_range = (-128, 128)
            
            slider = ttk.Scale(input_frame, from_=slider_range[0], to=slider_range[1], 
                             orient=tk.HORIZONTAL, length=180, style=f'{comp}.Horizontal.TScale')
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            slider.set(0)
            slider.bind('<B1-Motion>', lambda e, idx=i: self.on_lab_slider_change(idx))
            slider.bind('<ButtonRelease-1>', lambda e, idx=i: self.on_lab_slider_change(idx))
            self.lab_sliders.append(slider)
    
    def setup_control_panel(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(control_frame, text="Reset", command=self.reset_colors).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Random Color", command=self.random_color).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Color Picker", command=self.color_picker).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=10)
    
    def setup_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="Ready", font=('Segoe UI', 9), 
                                    foreground='#bbbbbb', background='#2b2b2b')
        self.status_label.pack(side=tk.LEFT)
        
        self.clipping_label = ttk.Label(status_frame, text="", font=('Segoe UI', 9), 
                                      foreground='#ff6b6b', background='#2b2b2b')
        self.clipping_label.pack(side=tk.RIGHT)
    
    def show_clipping_warning(self, message):
        self.clipping_label.config(text=message)
        self.clipping_warning_shown = True
        self.root.after(3000, self.hide_clipping_warning)
    
    def hide_clipping_warning(self):
        self.clipping_label.config(text="")
        self.clipping_warning_shown = False
    
    def update_status(self, message):
        self.status_label.config(text=message)
    
    def on_rgb_entry_change(self, index):
        if self.updating:
            return
        
        try:
            value = int(self.rgb_entries[index].get())
            if 0 <= value <= 255:
                self.current_rgb[index] = value
                self.rgb_sliders[index].set(value)
                self.rgb_labels[index].config(text=str(value))
                self.update_all_models()
                self.update_status("RGB values updated")
            else:
                self.show_clipping_warning("RGB values clipped to 0-255 range")
                clipped_value = max(0, min(255, value))
                self.current_rgb[index] = clipped_value
                self.rgb_sliders[index].set(clipped_value)
                self.rgb_labels[index].config(text=str(clipped_value))
                self.update_all_models()
        except ValueError:
            pass
    
    def on_rgb_slider_change(self, index):
        if self.updating:
            return
        
        value = int(self.rgb_sliders[index].get())
        self.current_rgb[index] = value
        self.rgb_entries[index].delete(0, tk.END)
        self.rgb_entries[index].insert(0, str(value))
        self.rgb_labels[index].config(text=str(value))
        self.update_all_models()
        self.update_status("RGB slider adjusted")
    
    def on_xyz_entry_change(self, index):
        if self.updating:
            return
        
        try:
            xyz = [float(self.xyz_entries[i].get()) for i in range(3)]
            rgb = ColorConverter.xyz_to_rgb(xyz)
            
            clipping_occurred = False
            for i in range(3):
                if rgb[i] < 0 or rgb[i] > 255:
                    clipping_occurred = True
                    break
            
            if clipping_occurred and not self.clipping_warning_shown:
                self.show_clipping_warning("Color clipped to RGB gamut")
            
            self.current_rgb = [max(0, min(255, int(c))) for c in rgb]
            self.update_all_models()
            self.update_status("XYZ values updated")
            
        except ValueError:
            pass
    
    def on_xyz_slider_change(self, index):
        if self.updating:
            return
        
        try:
            xyz = [self.xyz_sliders[i].get() for i in range(3)]
            rgb = ColorConverter.xyz_to_rgb(xyz)
            
            clipping_occurred = False
            for i in range(3):
                if rgb[i] < 0 or rgb[i] > 255:
                    clipping_occurred = True
                    break
            
            if clipping_occurred and not self.clipping_warning_shown:
                self.show_clipping_warning("Color clipped to RGB gamut")
            
            self.current_rgb = [max(0, min(255, int(c))) for c in rgb]
            
            self.updating = True
            for i in range(3):
                self.rgb_entries[i].delete(0, tk.END)
                self.rgb_entries[i].insert(0, str(self.current_rgb[i]))
                self.rgb_sliders[i].set(self.current_rgb[i])
                self.rgb_labels[i].config(text=str(self.current_rgb[i]))
            
            xyz_actual = ColorConverter.rgb_to_xyz(self.current_rgb)
            lab = ColorConverter.xyz_to_lab(xyz_actual)
            
            for i in range(3):
                self.lab_entries[i].delete(0, tk.END)
                self.lab_entries[i].insert(0, f"{lab[i]:.2f}")
                self.lab_sliders[i].set(lab[i])
                self.lab_labels[i].config(text=f"{lab[i]:.1f}")
            
            color_hex = f"#{self.current_rgb[0]:02x}{self.current_rgb[1]:02x}{self.current_rgb[2]:02x}"
            self.color_display.configure(bg=color_hex)
            self.hex_label.config(text=color_hex.upper())
            self.rgb_label.config(text=f"RGB({self.current_rgb[0]}, {self.current_rgb[1]}, {self.current_rgb[2]})")
            
            self.updating = False
            self.update_status("XYZ slider adjusted")
            
        except ValueError:
            pass
    
    def on_lab_entry_change(self, index):
        if self.updating:
            return
        
        try:
            lab = [float(self.lab_entries[i].get()) for i in range(3)]
            xyz = ColorConverter.lab_to_xyz(lab)
            rgb = ColorConverter.xyz_to_rgb(xyz)
            
            clipping_occurred = False
            for i in range(3):
                if rgb[i] < 0 or rgb[i] > 255:
                    clipping_occurred = True
                    break
            
            if clipping_occurred and not self.clipping_warning_shown:
                self.show_clipping_warning("Color clipped to RGB gamut")
            
            self.current_rgb = [max(0, min(255, int(c))) for c in rgb]
            self.update_all_models()
            self.update_status("LAB values updated")
            
        except ValueError:
            pass
    
    def on_lab_slider_change(self, index):
        if self.updating:
            return
        
        try:
            lab = [self.lab_sliders[i].get() for i in range(3)]
            xyz = ColorConverter.lab_to_xyz(lab)
            rgb = ColorConverter.xyz_to_rgb(xyz)
            
            clipping_occurred = False
            for i in range(3):
                if rgb[i] < 0 or rgb[i] > 255:
                    clipping_occurred = True
                    break
            
            if clipping_occurred and not self.clipping_warning_shown:
                self.show_clipping_warning("Color clipped to RGB gamut")
            
            self.current_rgb = [max(0, min(255, int(c))) for c in rgb]
            
            self.updating = True
            for i in range(3):
                self.rgb_entries[i].delete(0, tk.END)
                self.rgb_entries[i].insert(0, str(self.current_rgb[i]))
                self.rgb_sliders[i].set(self.current_rgb[i])
                self.rgb_labels[i].config(text=str(self.current_rgb[i]))
            
            xyz_actual = ColorConverter.rgb_to_xyz(self.current_rgb)
            for i in range(3):
                self.xyz_entries[i].delete(0, tk.END)
                self.xyz_entries[i].insert(0, f"{xyz_actual[i]:.2f}")
                self.xyz_sliders[i].set(xyz_actual[i])
                self.xyz_labels[i].config(text=f"{xyz_actual[i]:.1f}")
            
            color_hex = f"#{self.current_rgb[0]:02x}{self.current_rgb[1]:02x}{self.current_rgb[2]:02x}"
            self.color_display.configure(bg=color_hex)
            self.hex_label.config(text=color_hex.upper())
            self.rgb_label.config(text=f"RGB({self.current_rgb[0]}, {self.current_rgb[1]}, {self.current_rgb[2]})")
            
            self.updating = False
            self.update_status("LAB slider adjusted")
            
        except ValueError:
            pass
    
    def update_all_models(self):
        self.updating = True
        
        try:
            for i in range(3):
                self.rgb_entries[i].delete(0, tk.END)
                self.rgb_entries[i].insert(0, str(self.current_rgb[i]))
                self.rgb_sliders[i].set(self.current_rgb[i])
                self.rgb_labels[i].config(text=str(self.current_rgb[i]))
            
            xyz = ColorConverter.rgb_to_xyz(self.current_rgb)
            for i in range(3):
                self.xyz_entries[i].delete(0, tk.END)
                self.xyz_entries[i].insert(0, f"{xyz[i]:.2f}")
                self.xyz_sliders[i].set(xyz[i])
                self.xyz_labels[i].config(text=f"{xyz[i]:.1f}")
            
            lab = ColorConverter.xyz_to_lab(xyz)
            for i in range(3):
                self.lab_entries[i].delete(0, tk.END)
                self.lab_entries[i].insert(0, f"{lab[i]:.2f}")
                self.lab_sliders[i].set(lab[i])
                self.lab_labels[i].config(text=f"{lab[i]:.1f}")
            
            color_hex = f"#{self.current_rgb[0]:02x}{self.current_rgb[1]:02x}{self.current_rgb[2]:02x}"
            self.color_display.configure(bg=color_hex)
            self.hex_label.config(text=color_hex.upper())
            self.rgb_label.config(text=f"RGB({self.current_rgb[0]}, {self.current_rgb[1]}, {self.current_rgb[2]})")
            
        finally:
            self.updating = False
    
    def reset_colors(self):
        self.current_rgb = [128, 128, 128]
        self.update_all_models()
        self.update_status("Colors reset to default")
        self.hide_clipping_warning()
    
    def random_color(self):
        self.current_rgb = [np.random.randint(0, 256) for _ in range(3)]
        self.update_all_models()
        self.update_status("Random color generated")
        self.hide_clipping_warning()
    
    def color_picker(self):
        try:
            color_code = colorchooser.askcolor(initialcolor=(self.current_rgb[0], self.current_rgb[1], self.current_rgb[2]))
            
            if color_code[0] is not None:
                r, g, b = color_code[0]
                self.current_rgb = [int(r), int(g), int(b)]
                self.update_all_models()
                self.update_status("Color selected from picker")
                self.hide_clipping_warning()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open color picker: {str(e)}")
    
    def show_about(self):
        messagebox.showinfo("About", "Color Models Laboratory")

def main():
    root = tk.Tk()
    app = ModernColorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
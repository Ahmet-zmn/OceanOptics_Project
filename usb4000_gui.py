import tkinter as tk
from tkinter import messagebox, ttk, filedialog, colorchooser
import threading
import time
import sys
import os
import csv
import json
import subprocess
from datetime import datetime
import urllib.request

GITHUB_URL = "https://github.com/Ahmet-zmn/OceanOptics_Project"

# version.json dosyasindan surum bilgisini oku
def _load_app_version():
    try:
        vf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
        with open(vf, "r", encoding="utf-8") as f:
            return json.load(f).get("version", "1.0.0")
    except Exception:
        return "1.0.0"

APP_VERSION = _load_app_version()

# EXE (cx_Freeze) modunda çalışırken exe'nin klasörünü sys.path'e ekle
# Böylece 'oceandirect', 'languages' vb. yan klasörler bulunabilir
if getattr(sys, 'frozen', False):
    # cx_Freeze: executable'ın bulunduğu klasör
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    # Normal Python çalıştırma
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

# oceandirect klasörünü de doğrudan ekle (frozen modda import için)
_OCEAN_DIR = os.path.join(_BASE_DIR, "oceandirect")
if os.path.isdir(_OCEAN_DIR) and _OCEAN_DIR not in sys.path:
    sys.path.insert(0, _OCEAN_DIR)

# Tcl/Tk init.tcl hatası için — share/tcl8.6 klasörünü işaret et
_share = os.path.join(_BASE_DIR, "share")
for _entry in os.listdir(_share) if os.path.isdir(_share) else []:
    if _entry.startswith("tcl"):
        os.environ.setdefault("TCL_LIBRARY", os.path.join(_share, _entry))
    if _entry.startswith("tk"):
        os.environ.setdefault("TK_LIBRARY",  os.path.join(_share, _entry))

# Çalışma dizinini de exe'nin klasörüne taşı (config.json, data/ vb. için)
os.chdir(_BASE_DIR)


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Localization: imports now work directly from the local 'oceandirect' package
try:
    from oceandirect.OceanDirectAPI import OceanDirectAPI, OceanDirectError
    print("OceanDirect SDK successfully imported.")
except ImportError as e:
    print(f"Error importing OceanDirect SDK: {e}")
    messagebox.showerror("Import Error", "Please ensure the 'oceandirect' folder is in the same directory.")
    sys.exit(1)

class OceanOpticsGUI:
    def __init__(self, root):
        self.root = root
        self.device_lock = threading.Lock()
        
        self.config_file = "config.json"
        self.lang_dir = "languages"
        self.translations = {}
        self.omni_url = "" # Dynamic OmniDriver URL from GitHub
        self.lang = "tr"
        self._stop_update = False
        self._stop_download = False
        self.record_count = 0 
        self.save_path = ""
        self.log_format = "Timestamp"
        self.plot_styles = {}
        self.origin_version = "OriginLab"
        self.origin_exe = None
        
        self.load_all_translations()
        self.load_config()
        # self.find_origin_exe() # Moved logic
        # self.initialize_device() # Disable auto-connect
        self.root.after(100, lambda: self.find_origin_exe(silent=True))
        self.root.after(2000, lambda: self.check_for_updates(manual=False))
        
        self.root.title(self.get_text("title"))
        self.root.geometry("1000x920")
        
        self.api = OceanDirectAPI()
        self.device = None
        self.wavelengths = None
        self.running = False
        self.stop_requested = False
        self.is_recording = False
        self.thread = None
        self.last_saved_file = None
        self.mode = "Intensity"
        self.view_mode = "Intensity"
        self.available_devices = [] # List of (id, model)
        self.monitors = [] # Active wavelength monitor windows
        
        # Plot State
        self.dark_spectrum = None
        self.ref_spectrum = None
        self.mode = "Intensity" 
        self.view_mode = "Intensity" 
        
        # Parameters
        self.time_space_var = tk.StringVar(value="1.0")
        self.wait_ms_var = tk.StringVar(value="0")
        self.collect_time_var = tk.StringVar(value="10.0")
        self.time_unit_var = tk.StringVar(value=self.get_text("unit_sec"))
        self.filename_var = tk.StringVar(value="spectrum_data")
        self.log_format_var = tk.StringVar(value=self.log_format)
        
        self.setup_menu()
        self.setup_ui()
        self.update_ui_texts()

    def find_origin_exe(self, silent=True):
        paths = [r"C:\Program Files\OriginLab", r"C:\Program Files (x86)\OriginLab"]
        detected = []
        for base in paths:
            if os.path.exists(base):
                for item in os.listdir(base):
                    exe = os.path.join(base, item, "Origin64.exe")
                    if os.path.exists(exe):
                        detected.append((item, exe))
        if detected:
            detected.sort(key=lambda x: x[0], reverse=True)
            self.origin_version = detected[0][0]
            self.origin_exe = detected[0][1]
            if not silent: messagebox.showinfo("Origin", self.get_text("msg_origin_success").format(version=self.origin_version))
        else:
            if not silent: messagebox.showwarning("Origin", self.get_text("err_origin_not_found"))
            if not hasattr(self, 'origin_exe') or self.origin_exe is None:
                self.origin_version = "OriginLab"
                self.origin_exe = None
        self.save_config()

    def open_origin_settings(self):
        diag = tk.Toplevel(self.root)
        diag.title(self.get_text("menu_origin"))
        diag.geometry("400x200")
        diag.transient(self.root)
        diag.grab_set()

        lbl_curr = tk.Label(diag, text=self.get_text("lbl_origin_detected").format(version=self.origin_version), pady=10)
        lbl_curr.pack()

        def run_detect():
            self.find_origin_exe(silent=False)
            self.update_ui_texts()
            lbl_curr.config(text=self.get_text("lbl_origin_detected").format(version=self.origin_version))

        def run_manual():
            path = filedialog.askopenfilename(title=self.get_text("btn_origin_manual"), filetypes=[("Origin Executable", "Origin64.exe"), ("All Files", "*.*")])
            if path:
                self.origin_exe = path
                self.origin_version = os.path.basename(os.path.dirname(path))
                self.save_config()
                self.update_ui_texts()
                lbl_curr.config(text=self.get_text("lbl_origin_detected").format(version=self.origin_version))
                messagebox.showinfo("Origin", self.get_text("msg_origin_success").format(version=self.origin_version))

        tk.Button(diag, text=self.get_text("btn_origin_detect"), command=run_detect, width=25, pady=5).pack(pady=5)
        tk.Button(diag, text=self.get_text("btn_origin_manual"), command=run_manual, width=25, pady=5).pack(pady=5)
        tk.Button(diag, text=self.get_text("btn_close"), command=diag.destroy, width=15).pack(pady=10)

    def load_all_translations(self):
        if not os.path.exists(self.lang_dir): os.makedirs(self.lang_dir)
        found_files = [f for f in os.listdir(self.lang_dir) if f.endswith(".json")]
        if not found_files:
            self.translations["tr"] = {"title": "Spektrometre"}
            return
        for filename in found_files:
            lang_code = os.path.splitext(filename)[0]
            try:
                with open(os.path.join(self.lang_dir, filename), 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except Exception as e: print(f"Load error {filename}: {e}")

    def load_config(self):
        default_save_path = os.path.join(_BASE_DIR, "data")
        default_styles = {
            "dark": {"color": "#000000", "width": 1.5, "style": "-"},
            "ref": {"color": "#00BFFF", "width": 1.5, "style": "-"},
            "signal": {"color": "#0000FF", "width": 2.0, "style": "-"}
        }
        if not os.path.exists(default_save_path): os.makedirs(default_save_path)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.lang = config.get("lang", "tr")
                    self.save_path = config.get("save_path", default_save_path)
                    self.log_format = config.get("log_format", "ElapsedTime")
                    self.plot_styles = config.get("plot_styles", default_styles)
                    self.origin_exe = config.get("origin_exe", None)
                    self.origin_version = config.get("origin_version", "OriginLab")
                    self.last_saved_file = config.get("last_saved_file", None)
            except: 
                self.lang = "tr"; self.save_path = default_save_path; self.log_format = "ElapsedTime"; self.plot_styles = default_styles
                self.origin_exe = None; self.origin_version = "OriginLab"
        else: 
            self.lang = "tr"; self.save_path = default_save_path; self.log_format = "ElapsedTime"; self.plot_styles = default_styles
            self.origin_exe = None; self.origin_version = "OriginLab"
            self.save_config()
        if self.lang not in self.translations: self.lang = list(self.translations.keys())[0] if self.translations else "tr"

    def save_config(self):
        config = {
            "lang": self.lang, 
            "save_path": self.save_path, 
            "log_format": self.log_format, 
            "plot_styles": self.plot_styles,
            "origin_exe": self.origin_exe,
            "origin_version": self.origin_version,
            "last_saved_file": self.last_saved_file
        }
        try:
            with open(self.config_file, 'w') as f: json.dump(config, f, indent=4)
        except Exception as e: print(f"Save config error: {e}")

    def get_text(self, key, default=None):
        if self.lang in self.translations:
            return self.translations[self.lang].get(key, default if default is not None else key)
        return default if default is not None else key

    def setup_menu(self):
        self.menubar = tk.Menu(self.root)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.lang_menu = tk.Menu(self.settings_menu, tearoff=0)
        for lang_code in sorted(self.translations.keys()):
            label = lang_code.upper()
            if lang_code == "tr": label = "Türkçe"
            elif lang_code == "en": label = "English"
            self.lang_menu.add_command(label=label, command=lambda l=lang_code: self.change_language(l))
        self.settings_menu.add_cascade(label=self.get_text("menu_lang"), menu=self.lang_menu)
        
        self.rec_settings_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.rec_settings_menu.add_command(label=self.get_text("menu_save_path"), command=self.change_save_path)
        self.format_menu = tk.Menu(self.rec_settings_menu, tearoff=0)
        self.format_menu.add_radiobutton(label=self.get_text("log_elapsed"), variable=self.log_format_var, value="ElapsedTime", command=self.change_log_format)
        self.format_menu.add_radiobutton(label=self.get_text("log_timestamp"), variable=self.log_format_var, value="Timestamp", command=self.change_log_format)
        self.format_menu.add_radiobutton(label=self.get_text("log_sequential"), variable=self.log_format_var, value="Sequential", command=self.change_log_format)
        self.rec_settings_menu.add_cascade(label=self.get_text("menu_log_format"), menu=self.format_menu)
        self.settings_menu.add_cascade(label=self.get_text("menu_rec_settings"), menu=self.rec_settings_menu)
        
        self.settings_menu.add_command(label=self.get_text("menu_plot_settings"), command=self.open_plot_settings)
        self.settings_menu.add_command(label=self.get_text("menu_origin"), command=self.open_origin_settings)
        
        self.menubar.add_cascade(label=self.get_text("menu_settings"), menu=self.settings_menu)
        
        self.drivers_menu = tk.Menu(self.menubar, tearoff=0)
        self.drivers_menu.add_command(label=self.get_text("menu_setup_drivers"), command=self.open_driver_setup)
        self.menubar.add_cascade(label=self.get_text("menu_drivers"), menu=self.drivers_menu)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label=self.get_text("menu_about"), command=self.show_about)
        self.help_menu.add_command(label=self.get_text("menu_check_update"), command=self.check_for_updates)
        self.help_menu.add_command(label=self.get_text("btn_visit_github"), command=lambda: subprocess.Popen(f'start {GITHUB_URL}', shell=True))
        self.menubar.add_cascade(label=self.get_text("menu_help"), menu=self.help_menu)
        self.root.config(menu=self.menubar)

    def check_for_updates(self, manual=True):
        """GitHub üzerinden yeni versiyon kontrolü yapar."""
        v_url = GITHUB_URL.replace("github.com", "raw.githubusercontent.com") + "/main/version.json"
        
        def run_check():
            try:
                req = urllib.request.Request(v_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    server_v = data.get("version", "1.0.0")
                    self._update_exe_url = data.get("update_url", "")
                    self.omni_url = data.get("omni_driver_url", "")
                    
                    if server_v > APP_VERSION:
                        self.root.after(0, lambda: self.prompt_update(server_v))
                    elif manual:
                        msg = self.get_text("msg_up_to_date", "Software is up to date (Version: {version})").format(version=APP_VERSION)
                        self.root.after(0, lambda: messagebox.showinfo(self.get_text("menu_check_update"), msg))
            except Exception as e:
                if manual:
                    self.root.after(0, lambda: messagebox.showerror("Error", self.get_text("msg_update_error").format(error=str(e))))
        
        threading.Thread(target=run_check, daemon=True).start()

    def prompt_update(self, new_v):
        """Güncelleme bulundu penceresi"""
        update_win = tk.Toplevel(self.root)
        update_win.title(self.get_text("menu_check_update"))
        update_win.geometry("420x200")
        update_win.resizable(False, False)
        update_win.transient(self.root)
        update_win.grab_set()

        # Ekranda ortala
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        update_win.geometry(f"+{x}+{y}")

        msg = self.get_text("msg_update_found", "New version available: {version}").format(version=new_v)
        tk.Label(update_win, text=msg, pady=20, wraplength=380, font=("Segoe UI", 10)).pack()
        
        btn_frame = tk.Frame(update_win)
        btn_frame.pack(pady=10)

        def on_update():
            update_win.destroy()
            self.download_and_install_update(new_v)

        tk.Button(btn_frame, text=self.get_text("btn_update_now", "Update Now"), command=on_update,
                  width=15, bg="#0078D7", fg="white", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text=self.get_text("btn_update_later", "Later"), command=update_win.destroy,
                  width=15).pack(side=tk.LEFT, padx=10)

    def download_and_install_update(self, new_v):
        """GitHub veya Google Drive üzerinden güncel kurulum EXE'sini indir ve çalıştır."""
        exe_url = getattr(self, '_update_exe_url', '') or ''
        
        # Eğer link boşsa veya varsayılan GitHub linki gerekiyorsa
        if not exe_url:
            exe_url = GITHUB_URL + f"/releases/download/v{new_v}/OceanOptics_USB4000_Setup.exe"
            
        # Google Drive linki kontrolü ve dönüştürme (view -> uc?export=download)
        if "drive.google.com" in exe_url:
            if "/file/d/" in exe_url:
                file_id = exe_url.split("/file/d/")[1].split("/")[0]
                exe_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            elif "id=" not in exe_url and "/d/" in exe_url:
                # Alternatif format denemesi
                parts = exe_url.split("/")
                for i, p in enumerate(parts):
                    if p == "d" and i+1 < len(parts):
                        file_id = parts[i+1]
                        exe_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                        break
        
        temp_dir = os.environ.get("TEMP", os.getcwd())
        target_path = os.path.join(temp_dir, "OceanOptics_USB4000_Setup_Update.exe")
        
        def success():
            try:
                subprocess.Popen(f'"{target_path}"', shell=True)
                self.on_close()
            except Exception as e:
                self.log_update_error(f"Installation trigger failed: {str(e)}")
                messagebox.showerror("Error", f"Update installer could not be started: {e}")

        self.start_download(exe_url, target_path, self.get_text("menu_check_update"), success)

    def log_update_error(self, message):
        """Güncelleme hatalarını dosyaya kaydeder."""
        try:
            log_path = os.path.join(_BASE_DIR, "update_error_log.txt")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass

    def start_download(self, url, target_path, title, success_callback=None):
        """Genel amaçlı dosya indirme yardımcısı (İlerleme çubuklu)"""
        if not url:
            messagebox.showerror("Error", "URL not found.")
            return

        status_win = tk.Toplevel(self.root)
        status_win.title(title)
        status_win.geometry("400x160")
        status_win.resizable(False, False)
        status_win.transient(self.root)
        status_win.grab_set()

        # Center
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 80
        status_win.geometry(f"+{x}+{y}")

        status_label = tk.Label(status_win, text=self.get_text("msg_downloading"), pady=10, wraplength=350)
        status_label.pack()

        progress = ttk.Progressbar(status_win, orient=tk.HORIZONTAL, length=300, mode='determinate')
        progress.pack(pady=10)

        self._stop_download = False
        def on_cancel():
            self._stop_download = True
            status_win.destroy()

        cancel_btn = tk.Button(status_win, text="Cancel", command=on_cancel)
        cancel_btn.pack(pady=5)

        def progress_hook(count, block_size, total_size):
            if hasattr(self, '_stop_download') and self._stop_download:
                raise Exception("CANCEL_DL")
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                if percent > 100: percent = 100
                self.root.after(0, lambda p=percent: progress.config(value=p))
                self.root.after(0, lambda p=percent: status_label.config(text=f"{self.get_text('msg_downloading')} ({p}%)"))

        def run_dl():
            try:
                # User-Agent handling for some servers
                opener = urllib.request.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                urllib.request.install_opener(opener)
                
                urllib.request.urlretrieve(url, target_path, reporthook=progress_hook)
                self.root.after(0, status_win.destroy)
                if success_callback:
                    self.root.after(0, lambda: success_callback())
            except Exception as e:
                self.root.after(0, status_win.destroy)
                if "CANCEL_DL" not in str(e):
                    err_msg = self.get_text("msg_download_error", "Download error: {error}").format(error=str(e))
                    self.log_update_error(f"Download error from {url}: {str(e)}")
                    self.root.after(0, lambda m=err_msg: messagebox.showerror("Error", m))

        threading.Thread(target=run_dl, daemon=True).start()

    def change_language(self, lang):
        self.lang = lang; self.save_config()
        self.root.title(self.get_text("title"))
        self.update_menu_texts(); self.update_ui_texts()

    def update_menu_texts(self):
        self.menubar.entryconfig(1, label=self.get_text("menu_settings"))
        self.menubar.entryconfig(2, label=self.get_text("menu_drivers"))
        self.menubar.entryconfig(3, label=self.get_text("menu_help"))
        self.settings_menu.entryconfig(0, label=self.get_text("menu_lang"))
        self.settings_menu.entryconfig(1, label=self.get_text("menu_rec_settings"))
        self.settings_menu.entryconfig(2, label=self.get_text("menu_plot_settings"))
        self.settings_menu.entryconfig(3, label=self.get_text("menu_origin"))
        self.drivers_menu.entryconfig(0, label=self.get_text("menu_setup_drivers"))
        self.rec_settings_menu.entryconfig(0, label=self.get_text("menu_save_path"))
        self.rec_settings_menu.entryconfig(1, label=self.get_text("menu_log_format"))
        self.format_menu.entryconfig(0, label=self.get_text("log_timestamp"))
        self.format_menu.entryconfig(1, label=self.get_text("log_sequential"))
        self.help_menu.entryconfig(0, label=self.get_text("menu_about"))
        self.help_menu.entryconfig(1, label=self.get_text("menu_check_update"))
        self.help_menu.entryconfig(2, label=self.get_text("btn_visit_github"))

    def change_save_path(self):
        new_path = filedialog.askdirectory(initialdir=self.save_path, title=self.get_text("msg_save_path_title"))
        if new_path: self.save_path = new_path; self.save_config()

    def change_log_format(self):
        self.log_format = self.log_format_var.get(); self.save_config()

    def create_style_row(self, parent, key, controls):
        frame = tk.LabelFrame(parent, text=self.get_text(f"leg_{key}"), padx=10, pady=5)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Color
        tk.Label(frame, text=self.get_text("lbl_style_color")).grid(row=0, column=0, padx=5)
        color_btn = tk.Button(frame, bg=self.plot_styles[key]["color"], width=10)
        color_btn.config(command=lambda: self.pick_color(key, color_btn))
        color_btn.grid(row=0, column=1, padx=5)
        
        # Style
        tk.Label(frame, text=self.get_text("lbl_style_type")).grid(row=0, column=2, padx=5)
        styles = ["-", "--", ":", "-."]
        style_var = tk.StringVar(value=self.plot_styles[key]["style"])
        style_combo = ttk.Combobox(frame, textvariable=style_var, values=styles, state="readonly", width=10)
        style_combo.grid(row=0, column=3, padx=5)
        
        # Width
        tk.Label(frame, text=self.get_text("lbl_style_width")).grid(row=0, column=4, padx=5)
        width_var = tk.DoubleVar(value=self.plot_styles[key]["width"])
        width_spin = tk.Spinbox(frame, from_=0.5, to=10.0, increment=0.5, textvariable=width_var, width=5)
        width_spin.grid(row=0, column=5, padx=5)
        
        controls[key] = {"color_btn": color_btn, "style_var": style_var, "width_var": width_var}

    def open_plot_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title(self.get_text("menu_plot_settings"))
        settings_win.geometry("480x420")
        settings_win.grab_set()
        
        controls = {}
        for key in ["dark", "ref", "signal"]:
            self.create_style_row(settings_win, key, controls)

        def save_styles():
            for key in controls:
                self.plot_styles[key]["color"] = controls[key]["color_btn"]["bg"]
                self.plot_styles[key]["style"] = controls[key]["style_var"].get()
                self.plot_styles[key]["width"] = controls[key]["width_var"].get()
            self.save_config(); self.apply_plot_styles(); settings_win.destroy()

        tk.Button(settings_win, text=self.get_text("btn_save"), command=save_styles, 
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15).pack(pady=20)

    def pick_color(self, key, btn):
        color = colorchooser.askcolor(initialcolor=btn["bg"])[1]
        if color: btn.config(bg=color)

    def apply_plot_styles(self):
        # Update colors/styles for legend chips and plot lines
        self.canvas_dark.config(bg=self.plot_styles["dark"]["color"])
        self.canvas_ref.config(bg=self.plot_styles["ref"]["color"])
        self.canvas_signal.config(bg=self.plot_styles["signal"]["color"])
        
        self.dark_line.set_color(self.plot_styles["dark"]["color"])
        self.dark_line.set_linestyle(self.plot_styles["dark"]["style"])
        self.dark_line.set_linewidth(self.plot_styles["dark"]["width"])
        
        self.ref_line.set_color(self.plot_styles["ref"]["color"])
        self.ref_line.set_linestyle(self.plot_styles["ref"]["style"])
        self.ref_line.set_linewidth(self.plot_styles["ref"]["width"])
        
        self.line.set_color(self.plot_styles["signal"]["color"])
        self.line.set_linestyle(self.plot_styles["signal"]["style"])
        self.line.set_linewidth(self.plot_styles["signal"]["width"])
        self.canvas.draw_idle()

    def update_ui_texts(self):
        self.root.title(self.get_text("title"))
        self.stop_btn.config(text=self.get_text("btn_stop"))
        self.close_btn.config(text=self.get_text("btn_close"))
        self.dark_btn.config(text=self.get_text("btn_dark"))
        self.ref_btn.config(text=self.get_text("btn_ref"))
        self.sample_btn.config(text=self.get_text("btn_sample"))
        self.intensity_view_btn.config(text=self.get_text("btn_intensity_mode"))
        self.trans_view_btn.config(text=self.get_text("btn_trans_mode"))
        self.connect_btn.config(text=self.get_text("btn_connect"))
        self.refresh_btn.config(text=self.get_text("btn_refresh"))
        self.lbl_device_title.config(text=self.get_text("lbl_device"))
        
        if self.origin_exe and os.path.exists(self.origin_exe):
            self.open_origin_btn.config(text=self.get_text("btn_open_origin").format(version=self.origin_version), bg="#0078D7")
        else:
            self.open_origin_btn.config(text=self.get_text("btn_excel"), bg="#217346") # Excel Green
            
        self.open_records_btn.config(text=self.get_text("btn_open_records"))
        self.monitor_btn.config(text=self.get_text("btn_monitor"))
            
        self.lbl_time_space.config(text=self.get_text("lbl_time_space"))
        self.lbl_wait.config(text=self.get_text("lbl_wait"))
        self.lbl_total_time.config(text=self.get_text("lbl_total_time"))
        self.lbl_filename.config(text=self.get_text("lbl_filename"))
        self.lbl_leg_dark.config(text=self.get_text("leg_dark"))
        self.lbl_leg_ref.config(text=self.get_text("leg_ref"))
        self.lbl_leg_signal.config(text=self.get_text("leg_signal"))
        new_units = [self.get_text("unit_sec"), self.get_text("unit_min"), self.get_text("unit_hour")]
        self.time_unit_combo['values'] = new_units
        if not self.is_recording: self.status_label.config(text=self.get_text("lbl_status_monitoring"))
        elif self.ref_spectrum is not None: self.status_label.config(text=self.get_text("lbl_status_sample"))
        elif self.dark_spectrum is not None: self.status_label.config(text=self.get_text("lbl_status_ref"))
        else: self.status_label.config(text=self.get_text("lbl_status_dark"))
        self.ax.set_xlabel(self.get_text("plot_xlabel")); self.refresh_plot_visibility(); self.canvas.draw_idle()

    def show_about(self):
        about_win = tk.Toplevel(self.root)
        about_win.title(self.get_text("menu_about"))
        about_win.geometry("400x200")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        # Center
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        about_win.geometry(f"+{x}+{y}")

        tk.Label(about_win, text=self.get_text("title"), font=("Arial", 11, "bold"), pady=10).pack()
        
        info_text = f"Developed by: Ahmet ÖZMEN\nVersion: {APP_VERSION}"
        if self.lang == "tr": info_text = f"Hazırlayan: Ahmet ÖZMEN\nSürüm: {APP_VERSION}"
        
        tk.Label(about_win, text=info_text, pady=5).pack()
        
        link = tk.Label(about_win, text=GITHUB_URL, fg="blue", cursor="hand2", pady=10)
        link.pack()
        link.bind("<Button-1>", lambda e: subprocess.Popen(f'start {GITHUB_URL}', shell=True))

        tk.Button(about_win, text=self.get_text("btn_close"), command=about_win.destroy, width=10).pack(pady=10)

    def setup_ui(self):
        control_panel = tk.Frame(self.root, pady=10); control_panel.pack(side=tk.TOP, fill=tk.X)
        
        # Connection Panel
        conn_frame = tk.Frame(control_panel); conn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))
        self.lbl_device_title = tk.Label(conn_frame, text=self.get_text("lbl_device"), font=("Arial", 11, "bold"))
        self.lbl_device_title.pack(side=tk.LEFT, padx=5)
        
        self.device_combo = ttk.Combobox(conn_frame, state="readonly", width=30, font=("Arial", 11))
        self.device_combo.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = tk.Button(conn_frame, text=self.get_text("btn_refresh"), command=self.refresh_devices, bg="#607D8B", fg="white", font=("Arial", 10), width=12)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = tk.Button(conn_frame, text=self.get_text("btn_connect"), command=self.initialize_device, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=10)
        
        # Initial scan
        self.root.after(500, self.refresh_devices)

        btn_frame = tk.Frame(control_panel); btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        self.stop_btn = tk.Button(btn_frame, text=self.get_text("btn_stop"), command=self.stop_acquisition, bg="#f44336", fg="white", font=("Arial", 12, "bold"), width=12, state=tk.DISABLED, cursor="arrow")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.intensity_view_btn = tk.Button(btn_frame, text=self.get_text("btn_intensity_mode"), command=lambda: self.switch_view_mode("Intensity"), bg="#607D8B", fg="white", font=("Arial", 11, "bold"), width=16, cursor="arrow")
        self.intensity_view_btn.pack(side=tk.LEFT, padx=(20, 5))
        self.trans_view_btn = tk.Button(btn_frame, text=self.get_text("btn_trans_mode"), command=lambda: self.switch_view_mode("Transmission"), bg="#607D8B", fg="white", font=("Arial", 11, "bold"), width=16, cursor="arrow")
        self.trans_view_btn.pack(side=tk.LEFT, padx=5)
        self.open_origin_btn = tk.Button(btn_frame, text=self.get_text("btn_open_origin"), command=self.open_last_in_origin, bg="#0078D7", fg="white", font=("Arial", 11, "bold"), width=16, cursor="arrow")
        self.open_origin_btn.pack(side=tk.LEFT, padx=(20, 5))
        self.open_records_btn = tk.Button(btn_frame, text=self.get_text("btn_open_records"), command=self.open_records_folder, bg="#4DB6AC", fg="white", font=("Arial", 11, "bold"), width=14, cursor="arrow")
        self.open_records_btn.pack(side=tk.LEFT, padx=5)
        self.monitor_btn = tk.Button(btn_frame, text=self.get_text("btn_monitor"), command=self.open_monitor, bg="#FFEB3B", fg="black", font=("Arial", 11, "bold"), width=12, cursor="arrow")
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        self.close_btn = tk.Button(btn_frame, text=self.get_text("btn_close"), command=self.on_close, bg="#555555", fg="white", font=("Arial", 12, "bold"), width=12, cursor="arrow")
        self.close_btn.pack(side=tk.RIGHT, padx=5)
        trans_frame = tk.LabelFrame(control_panel, text="Transmission Workflow", pady=10); trans_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        self.dark_btn = tk.Button(trans_frame, text=self.get_text("btn_dark"), command=self.measure_dark, bg="#9C27B0", fg="white", font=("Arial", 10, "bold"), width=15, cursor="arrow")
        self.dark_btn.pack(side=tk.LEFT, padx=10); self.ref_btn = tk.Button(trans_frame, text=self.get_text("btn_ref"), command=self.measure_reference, bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=15, state=tk.DISABLED, cursor="arrow")
        self.ref_btn.pack(side=tk.LEFT, padx=10); self.sample_btn = tk.Button(trans_frame, text=self.get_text("btn_sample"), command=self.measure_sample, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), width=15, state=tk.DISABLED, cursor="arrow")
        self.sample_btn.pack(side=tk.LEFT, padx=10); self.status_label = tk.Label(trans_frame, text=self.get_text("lbl_status_monitoring"), fg="#666", font=("Arial", 9, "italic")); self.status_label.pack(side=tk.LEFT, padx=20)
        params_frame = tk.Frame(control_panel, pady=10); params_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        self.lbl_time_space = tk.Label(params_frame, text=self.get_text("lbl_time_space")); self.lbl_time_space.grid(row=0, column=0, sticky="e", padx=5)
        self.time_space_entry = tk.Entry(params_frame, textvariable=self.time_space_var, width=8); self.time_space_entry.grid(row=0, column=1, padx=5)
        self.lbl_wait = tk.Label(params_frame, text=self.get_text("lbl_wait")); self.lbl_wait.grid(row=0, column=2, sticky="e", padx=5)
        self.wait_entry = tk.Entry(params_frame, textvariable=self.wait_ms_var, width=8); self.wait_entry.grid(row=0, column=3, padx=5)
        self.lbl_total_time = tk.Label(params_frame, text=self.get_text("lbl_total_time")); self.lbl_total_time.grid(row=0, column=4, sticky="e", padx=5)
        self.collect_time_entry = tk.Entry(params_frame, textvariable=self.collect_time_var, width=8); self.collect_time_entry.grid(row=0, column=5, padx=5)
        self.time_unit_combo = ttk.Combobox(params_frame, textvariable=self.time_unit_var, values=[self.get_text("unit_sec"), self.get_text("unit_min"), self.get_text("unit_hour")], width=10, state="readonly"); self.time_unit_combo.grid(row=0, column=6, padx=5)
        self.lbl_filename = tk.Label(params_frame, text=self.get_text("lbl_filename")); self.lbl_filename.grid(row=0, column=7, sticky="e", padx=5); self.filename_entry = tk.Entry(params_frame, textvariable=self.filename_var, width=15); self.filename_entry.grid(row=0, column=8, padx=5)
        feedback_frame = tk.Frame(control_panel, pady=5); feedback_frame.pack(side=tk.TOP, fill=tk.X, padx=15); self.progress_var = tk.DoubleVar(); self.progress_bar = ttk.Progressbar(feedback_frame, variable=self.progress_var, maximum=100); self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)); self.completion_label = tk.Label(feedback_frame, text="", font=("Arial", 10, "bold"), fg="#4CAF50"); self.completion_label.pack(side=tk.LEFT)

        legend_frame = tk.Frame(self.root, pady=5); legend_frame.pack(side=tk.TOP, fill=tk.X, padx=15)
        self.canvas_dark = tk.Canvas(legend_frame, width=20, height=10, bg=self.plot_styles["dark"]["color"], highlightthickness=0); self.canvas_dark.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_leg_dark = tk.Label(legend_frame, text=self.get_text("leg_dark"), font=("Arial", 9)); self.lbl_leg_dark.pack(side=tk.LEFT, padx=(0, 20))
        self.canvas_ref = tk.Canvas(legend_frame, width=20, height=10, bg=self.plot_styles["ref"]["color"], highlightthickness=0); self.canvas_ref.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_leg_ref = tk.Label(legend_frame, text=self.get_text("leg_ref"), font=("Arial", 9)); self.lbl_leg_ref.pack(side=tk.LEFT, padx=(0, 20))
        self.canvas_signal = tk.Canvas(legend_frame, width=20, height=10, bg=self.plot_styles["signal"]["color"], highlightthickness=0); self.canvas_signal.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_leg_signal = tk.Label(legend_frame, text=self.get_text("leg_signal"), font=("Arial", 9, "bold")); self.lbl_leg_signal.pack(side=tk.LEFT)
        
        self.fig = Figure(figsize=(8, 6), dpi=100); self.ax = self.fig.add_subplot(111); self.ax.grid(True)
        self.dark_line, = self.ax.plot([], [], lw=self.plot_styles["dark"]["width"], color=self.plot_styles["dark"]["color"], ls=self.plot_styles["dark"]["style"], alpha=0.7)
        self.ref_line, = self.ax.plot([], [], lw=self.plot_styles["ref"]["width"], color=self.plot_styles["ref"]["color"], ls=self.plot_styles["ref"]["style"], alpha=0.7)
        self.line, = self.ax.plot([], [], lw=self.plot_styles["signal"]["width"], color=self.plot_styles["signal"]["color"], ls=self.plot_styles["signal"]["style"])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root); self.canvas.draw(); self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def set_busy_cursor(self, busy):
        cursor = "watch" if busy else ""; self.root.config(cursor=cursor); self.root.update_idletasks()

    def refresh_devices(self):
        self.set_busy_cursor(True)
        try:
            with self.device_lock:
                device_count = self.api.find_usb_devices()
                if device_count == 0:
                    self.available_devices = []
                    self.device_combo['values'] = ["No devices found"]
                    self.device_combo.current(0)
                    self.connect_btn.config(state=tk.DISABLED)
                else:
                    device_ids = self.api.get_device_ids()
                    self.available_devices = []
                    combo_values = []
                    for d_id in device_ids:
                        temp_device = self.api.open_device(d_id)
                        model = temp_device.get_model()
                        serial = temp_device.get_serial_number()
                        # Do NOT call close_device here, it invalidates the ID in this SDK
                        self.available_devices.append((d_id, model, serial))
                        combo_values.append(f"{model} ({serial})")
                    
                    self.device_combo['values'] = combo_values
                    self.device_combo.current(0)
                    self.connect_btn.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Refresh error: {e}")
        finally:
            self.set_busy_cursor(False)

    def initialize_device(self):
        selection_idx = self.device_combo.current()
        if selection_idx < 0 or not self.available_devices:
            messagebox.showwarning("Device", "Please select a device first.")
            return

        selected_id = self.available_devices[selection_idx][0]
        print(f"Connecting to device ID: {selected_id}")
        self.set_busy_cursor(True)
        try:
            with self.device_lock:
                self.device = self.api.open_device(selected_id)
                self.device_model = self.device.get_model()
                self.wavelengths = self.device.get_wavelengths()
                self.device_combo.config(state=tk.DISABLED)
                self.refresh_btn.config(state=tk.DISABLED)
                self.connect_btn.config(state=tk.DISABLED, bg="#888")
            self.ax.set_xlim(min(self.wavelengths), max(self.wavelengths)); self.refresh_plot_visibility(); self.start_acquisition(is_recording=False)
        except OceanDirectError as e:
            messagebox.showerror("Error", f"Connection failed: {e}")
        finally:
            self.set_busy_cursor(False)

    def setup_simulation(self):
        self.wavelengths = np.linspace(340, 1020, 3648); self.ax.set_xlim(340, 1020); self.refresh_plot_visibility(); self.start_acquisition(is_recording=False)

    def set_inputs_state(self, state):
        for w in [self.time_space_entry, self.wait_entry, self.collect_time_entry, self.time_unit_combo, self.filename_entry]: w.config(state=state)

    def measure_dark(self):
        self.set_busy_cursor(True)
        if self.running: self.stop_requested = True; self.running = False; time.sleep(0.6)
        messagebox.showinfo(self.get_text("msg_dark_title"), self.get_text("msg_dark_text"))
        try:
            with self.device_lock:
                if self.device: self.dark_spectrum = np.array(self.device.get_spectrum())
                else: self.dark_spectrum = np.random.normal(1000, 50, len(self.wavelengths))
            self.save_calibration_to_csv("dark_calibration", self.dark_spectrum); self.dark_line.set_data(self.wavelengths, self.dark_spectrum)
            self.dark_line.set_visible(self.view_mode == "Intensity"); self.canvas.draw()
            self.status_label.config(text=self.get_text("lbl_status_ref"), fg="#FF9800"); self.ref_btn.config(state=tk.NORMAL)
        except Exception as e: messagebox.showerror("Error", str(e))
        self.start_acquisition(is_recording=False); self.set_busy_cursor(False)

    def measure_reference(self):
        if self.dark_spectrum is None: return
        self.set_busy_cursor(True)
        if self.running: self.stop_requested = True; self.running = False; time.sleep(0.6)
        messagebox.showinfo(self.get_text("msg_ref_title"), self.get_text("msg_ref_text"))
        try:
            with self.device_lock:
                if self.device: self.ref_spectrum = np.array(self.device.get_spectrum())
                else:
                    self.ref_spectrum = np.random.normal(40000, 500, len(self.wavelengths))
                    self.ref_spectrum += 10000 * np.sin(self.wavelengths/100)
            self.save_calibration_to_csv("ref_calibration", self.ref_spectrum); self.ref_line.set_data(self.wavelengths, self.ref_spectrum)
            self.ref_line.set_visible(self.view_mode == "Intensity"); self.canvas.draw()
            self.status_label.config(text=self.get_text("lbl_status_sample"), fg="#2196F3"); self.sample_btn.config(state=tk.NORMAL)
        except Exception as e: messagebox.showerror("Error", str(e))
        self.start_acquisition(is_recording=False); self.set_busy_cursor(False)

    def save_calibration_to_csv(self, type_name, spectrum):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S'); filename = f"{type_name}_{timestamp}.csv"; full_path = os.path.join(self.save_path, filename); self.last_saved_file = full_path; self.save_config()
        if not os.path.exists(self.save_path): os.makedirs(self.save_path)
        try:
            with open(full_path, mode='w', newline='') as file:
                writer = csv.writer(file); writer.writerow(['Wavelength', 'Intensity'])
                for w, i in zip(self.wavelengths, spectrum): writer.writerow([f"{w:.2f}", f"{i:.2f}"])
        except Exception as e: print(f"File error: {e}")

    def measure_sample(self):
        if self.ref_spectrum is None: return
        self.set_busy_cursor(True); self.stop_requested = True; self.running = False; time.sleep(0.6); self.mode = "Transmission"; self.view_mode = "Transmission"; self.start_acquisition(is_recording=True)

    def switch_view_mode(self, mode):
        self.view_mode = mode; self.refresh_plot_visibility(); self.canvas.draw_idle()

    def refresh_plot_visibility(self):
        if self.view_mode == "Intensity":
            self.intensity_view_btn.config(relief=tk.SUNKEN, bg="#455A64"); self.trans_view_btn.config(relief=tk.RAISED, bg="#607D8B")
            self.ax.set_title(self.get_text("plot_title")); self.ax.set_ylabel(self.get_text("plot_ylabel")); self.ax.set_ylim(-100, 65535)
            self.dark_line.set_visible(self.dark_spectrum is not None); self.ref_line.set_visible(self.ref_spectrum is not None)
            if self.dark_spectrum is not None: self.dark_line.set_data(self.wavelengths, self.dark_spectrum)
            if self.ref_spectrum is not None: self.ref_line.set_data(self.wavelengths, self.ref_spectrum)
        else:
            self.intensity_view_btn.config(relief=tk.RAISED, bg="#607D8B"); self.trans_view_btn.config(relief=tk.SUNKEN, bg="#455A64")
            self.ax.set_title(self.get_text("plot_trans_title")); self.ax.set_ylabel("Transmission (%)"); self.ax.set_ylim(-10, 110)
            self.dark_line.set_visible(False); self.ref_line.set_visible(False)

    def start_acquisition(self, is_recording=False):
        if not self.running:
            self.is_recording = is_recording
            if is_recording:
                try:
                    self.t_space = float(self.time_space_var.get()); self.w_ms = float(self.wait_ms_var.get()); raw_time = float(self.collect_time_var.get()); unit = self.time_unit_var.get()
                    is_min = any(l.get("unit_min") == unit for l in self.translations.values()); is_hour = any(l.get("unit_hour") == unit for l in self.translations.values())
                    self.c_time = raw_time * 60 if is_min else (raw_time * 3600 if is_hour else raw_time); self.fname = self.filename_var.get().strip()
                    if not self.fname: raise ValueError(self.get_text("err_fname_empty"))
                except ValueError as e: messagebox.showerror(self.get_text("err_param"), str(e)); self.set_busy_cursor(False); return
                self.stop_btn.config(state=tk.NORMAL); self.set_inputs_state(tk.DISABLED); self.dark_btn.config(state=tk.DISABLED); self.ref_btn.config(state=tk.DISABLED); self.sample_btn.config(state=tk.DISABLED); self.status_label.config(text=self.get_text("lbl_status_running"), fg="#4CAF50")
            else:
                self.t_space = 0.5; self.w_ms = 0; self.status_label.config(text=self.get_text("lbl_status_monitoring"), fg="#666")
            self.running = True; self.stop_requested = False; self.completion_label.config(text=""); self.progress_var.set(0); self.thread = threading.Thread(target=self.acquisition_loop, daemon=True); self.thread.start()

    def stop_acquisition(self):
        self.set_busy_cursor(False); self.stop_requested = True; self.running = False; self.is_recording = False
        self.stop_btn.config(state=tk.DISABLED); self.set_inputs_state(tk.NORMAL); self.dark_btn.config(state=tk.NORMAL)
        if self.dark_spectrum is not None: self.ref_btn.config(state=tk.NORMAL)
        if self.ref_spectrum is not None: self.sample_btn.config(state=tk.NORMAL)
        self.root.after(800, lambda: self.start_acquisition(is_recording=False))

    def acquisition_loop(self):
        start_time = time.time(); index_counter = 0
        
        # Ensure wavelengths exist for simulation or monitor indexing
        if self.wavelengths is None:
            self.wavelengths = np.linspace(200, 1100, 3648)
            self.root.after(0, lambda: self.ax.set_xlim(200, 1100))
            
        if self.is_recording and self.w_ms > 0: time.sleep(self.w_ms / 1000.0)
        file = None; writer = None
        if self.is_recording:
            start_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S'); csv_filename = f"{self.fname}_{self.mode}_{start_timestamp}.csv"; full_path = os.path.join(self.save_path, csv_filename); self.last_saved_file = full_path; self.save_config()
            if not os.path.exists(self.save_path): os.makedirs(self.save_path)
            try:
                file = open(full_path, mode='w', newline=''); writer = csv.writer(file)
                label = "Time (s)" if self.log_format == "ElapsedTime" else ("Index" if self.log_format == "Sequential" else "Timestamp")
                writer.writerow([label] + [f"{w:.2f}" for w in self.wavelengths])
            except Exception as e: print(f"File error: {e}"); return
        next_sample_time = time.time()
        while not self.stop_requested:
            current_time = time.time()
            if self.is_recording:
                elapsed = current_time - start_time; progress = min((elapsed / self.c_time) * 100, 100); self.root.after(0, self.progress_var.set, progress)
                if elapsed >= self.c_time: self.root.after(0, self.completion_label.config, {"text": self.get_text("msg_finished")}); self.root.after(0, self.set_busy_cursor, False); break
            if current_time >= next_sample_time:
                try:
                    with self.device_lock:
                        if self.device: spectrum = np.array(self.device.get_spectrum())
                        else:
                            spectrum = np.random.normal(20000, 300, len(self.wavelengths)); spectrum *= (1 - 0.8 * np.exp(-((self.wavelengths - 500)**2) / 5000))
                    if spectrum is not None:
                        intensity_val = spectrum; trans_val = None
                        if self.dark_spectrum is not None and self.ref_spectrum is not None:
                            denom = (self.ref_spectrum - self.dark_spectrum); denom[denom == 0] = 1; trans_val = ((spectrum - self.dark_spectrum) / denom) * 100.0
                        plot_data = trans_val if (self.view_mode == "Transmission" and trans_val is not None) else intensity_val
                        if self.is_recording and writer:
                            index_counter += 1
                            if self.log_format == "ElapsedTime":
                                key = f"{(index_counter - 1) * self.t_space:.3f}"
                            elif self.log_format == "Sequential":
                                key = str(index_counter)
                            else:
                                key = datetime.now().isoformat()
                            
                            save_data = trans_val if (self.mode == "Transmission" and trans_val is not None) else intensity_val
                            writer.writerow([key] + list(save_data)); file.flush()
                        self.root.after(0, self.update_plot, plot_data)
                        # Broadcast to monitors
                        if self.monitors:
                            for mon in self.monitors:
                                self.root.after(0, mon.update_data, self.wavelengths, plot_data)
                    next_sample_time += self.t_space
                except Exception as e: print(f"Loop error: {e}"); break
            time.sleep(0.01)
        if file: file.close()
        if self.is_recording: self.root.after(0, self.stop_acquisition)
        else: self.running = False

    def open_monitor(self):
        mon = WavelengthMonitor(self.root, self)
        self.monitors.append(mon)

    def open_records_folder(self):
        if os.path.exists(self.save_path):
            try:
                os.startfile(self.save_path)
            except Exception as e: messagebox.showerror("Error", f"Could not open folder: {e}")
        else: messagebox.showwarning("Warning", "Save folder does not exist.")

    def open_last_in_origin(self):
        if self.is_recording:
            messagebox.showwarning("Warning", "Measurement in progress. Please wait until finished.")
            return

        target_file = self.last_saved_file
        
        # Eğer hafızada kayıt yoksa veya dosya silindiyse klasördeki en yeniyi bul
        if not target_file or not os.path.exists(target_file):
            if os.path.exists(self.save_path):
                files = [os.path.join(self.save_path, f) for f in os.listdir(self.save_path) if f.lower().endswith('.csv')]
                if files:
                    # mtime (modification time) daha güvenli, ctime (creation) bazen garip davranabilir
                    target_file = max(files, key=os.path.getmtime)
        
        if target_file and os.path.exists(target_file):
            target_file = os.path.abspath(target_file)
            try:
                if self.origin_exe and os.path.exists(self.origin_exe):
                    labtalk_cmd = f'open -w "{target_file}"'
                    subprocess.Popen([self.origin_exe, "-oc", labtalk_cmd])
                else:
                    os.startfile(target_file)
            except Exception as e: 
                messagebox.showerror("Error", f"Could not open file: {e}")
        else: 
            messagebox.showwarning("Warning", self.get_text("msg_no_measurements") if hasattr(self, 'get_text') else "No measurement file found.")

    def update_plot(self, data):
        self.line.set_data(self.wavelengths, data)
        if self.view_mode == "Intensity":
            max_val = np.max(data)
            if max_val > 0:
                curr = self.ax.get_ylim()
                if max_val > curr[1] * 0.9 or max_val < curr[1] * 0.3: self.ax.set_ylim(-100, max_val * 1.2)
        self.canvas.draw_idle()

    def open_driver_setup(self):
        DriverInstallationDialog(self.root, self)

    def on_close(self):
        self.stop_requested = True; self.running = False
        if self.device:
            with self.device_lock:
                try: 
                    self.device.close_device()
                except: pass
        try:
            self.api.shutdown()
        except: pass
        self.root.destroy()

class DriverInstallationDialog:
    def __init__(self, parent, gui):
        self.gui = gui
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(gui.get_text("msg_driver_dialog_title", "Choose Spectrometer Driver"))
        self.dialog.geometry("500x400")
        self.dialog.grab_set()
        
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text=gui.get_text("msg_driver_dialog_title", "Choose Spectrometer Driver"), font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = tk.Scrollbar(list_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, font=("Arial", 10), yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)
        
        # Scan for drivers
        self.drivers = [] # list of (display_name, full_path)
        self.scan_drivers()
        
        for name, _ in self.drivers:
            self.listbox.insert(tk.END, name)
            
        btn_frame = tk.Frame(main_frame, pady=10)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text=gui.get_text("menu_setup_drivers", "Install Driver"), command=self.install_selected, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=gui.get_text("btn_install_sdk", "Install SDK"), command=self.install_sdk, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), width=15).pack(side=tk.LEFT, padx=5)
        
        # New "Fetch All Drivers" button
        tk.Button(btn_frame, text=gui.get_text("btn_fetch_drivers", "Fetch All Drivers"), command=self.fetch_all_drivers, bg="#FF9800", fg="white", font=("Arial", 10, "bold"), width=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text=gui.get_text("btn_close", "Close"), command=self.dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)

    def scan_drivers(self):
        winusb_path = os.path.join(os.getcwd(), "winusb")
        folders = ["winusb_driver", "winusb_driver_offline"]
        
        self.drivers = []
        for folder in folders:
            folder_path = os.path.join(winusb_path, folder)
            if not os.path.exists(folder_path): continue
            
            for file in os.listdir(folder_path):
                if file.lower().endswith(".inf"):
                    display_name = f"{folder} / {file}"
                    full_path = os.path.join(folder_path, file)
                    self.drivers.append((display_name, full_path))
        
        # Refresh listbox
        if hasattr(self, 'listbox'):
            self.listbox.delete(0, tk.END)
            for name, _ in self.drivers:
                self.listbox.insert(tk.END, name)
            if not self.drivers:
                self.listbox.insert(tk.END, "No drivers found. Click 'Fetch All Drivers'.")

    def fetch_all_drivers(self):
        # Full WinUSB driver pack (usually as a zip on GitHub for easier download)
        zip_url = GITHUB_URL + "/raw/main/winusb/winusb_pack.zip"
        winusb_path = os.path.join(os.getcwd(), "winusb")
        target_zip = os.path.join(winusb_path, "winusb_pack.zip")
        
        if not os.path.exists(winusb_path): os.makedirs(winusb_path)

        def on_success():
            try:
                # Extract zip into winusb_driver subdirectory
                winusb_driver_path = os.path.join(winusb_path, "winusb_driver")
                if not os.path.exists(winusb_driver_path): os.makedirs(winusb_driver_path)
                
                import zipfile
                with zipfile.ZipFile(target_zip, 'r') as zip_ref:
                    zip_ref.extractall(winusb_driver_path)
                
                os.remove(target_zip)
                messagebox.showinfo("Success", self.gui.get_text("msg_drivers_success"))
                self.gui.root.after(0, self.scan_drivers)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract drivers: {e}")

        self.gui.start_download(zip_url, target_zip, self.gui.get_text("msg_downloading_drivers"), on_success)

    def install_selected(self):
        idx = self.listbox.curselection()
        if not idx: return
        
        _, inf_path = self.drivers[idx[0]]
        
        confirm = messagebox.askyesno("Confirm", f"Attempting to install:\n{inf_path}\n\nThis REQUIRES Administrator rights. Proceed?")
        if not confirm: return
        
        self.gui.set_busy_cursor(True)
        try:
            ps_cmd = f'Start-Process -FilePath "pnputil" -ArgumentList "/add-driver", """{inf_path}""", "/install" -Verb RunAs -Wait'
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=0x08000000)
            
            if result.returncode == 0:
                messagebox.showinfo("Success", self.gui.get_text("msg_install_success"))
            else:
                messagebox.showwarning("Notice", f"PNPUtil returned {result.returncode}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.gui.set_busy_cursor(False)

    def install_sdk(self):
        installer_path = os.path.join(os.getcwd(), "winusb", "OmniDriver-2.80-win64-installer.exe")
        
        if os.path.exists(installer_path):
            # Just run it
            confirm = messagebox.askyesno("Confirm", f"Found installer. Run now?\n{installer_path}")
            if confirm:
                ps_cmd = f'Start-Process -FilePath "{installer_path}" -Verb RunAs'
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], creationflags=0x08000000)
            return

        # Use URL from version.json if fetched, else fallback to hardcoded
        omni_url = getattr(self.gui, 'omni_url', "")
        if not omni_url:
            omni_url = "https://www.oceanoptics.com/wp-content/uploads/2026/01/OmniDriver-2.80-win64-installer.exe"
        
        def on_success():
            ps_cmd = f'Start-Process -FilePath "{installer_path}" -Verb RunAs'
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
            subprocess.run(cmd, creationflags=0x08000000)
            messagebox.showinfo("Success", self.gui.get_text("msg_install_success"))

        self.gui.start_download(omni_url, installer_path, self.gui.get_text("msg_downloading_omni"), on_success)

class WavelengthMonitor:
    def __init__(self, parent, gui):
        self.gui = gui
        self.window = tk.Toplevel(parent)
        self.window.title(gui.get_text("monitor_title", "Wavelength Monitor"))
        self.window.geometry("500x550")
        
        # History data
        self.history_x = []
        self.history_y = []
        self.start_time = time.time()
        self.max_points = 100 # User requested 100 data points sliding window
        
        main_frame = tk.Frame(self.window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input section
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(input_frame, text=gui.get_text("lbl_monitor_wavelength", "Wavelength (nm):"), font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.wl_var = tk.StringVar(value="500.0")
        self.entry = tk.Entry(input_frame, textvariable=self.wl_var, font=("Arial", 11), width=8, justify="center")
        self.entry.grid(row=0, column=1, padx=5)
        
        tk.Label(input_frame, text=gui.get_text("lbl_monitor_ymax", "Y-Max:"), font=("Arial", 10)).grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.ymax_var = tk.StringVar(value="110.0")
        self.ymax_entry = tk.Entry(input_frame, textvariable=self.ymax_var, font=("Arial", 11), width=8, justify="center")
        self.ymax_entry.grid(row=0, column=3, padx=5)
        
        self.val_label = tk.Label(input_frame, text="---", font=("Arial", 16, "bold"), fg="#D32F2F")
        self.val_label.grid(row=0, column=4, padx=(20, 0))
        
        # Plot section
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Wavelength Trend")
        self.ax.set_xlabel("Time (s)")
        self.ax.grid(True)
        self.line, = self.ax.plot([], [], lw=2, color="#2196F3")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_data(self, wavelengths, data):
        try:
            target_wl = float(self.wl_var.get())
            val = np.interp(target_wl, wavelengths, data)
            self.val_label.config(text=f"{val:.3f}")
            
            # Update history
            cur_time = time.time() - self.start_time
            self.history_x.append(cur_time)
            self.history_y.append(val)
            
            if len(self.history_x) > self.max_points:
                self.history_x.pop(0)
                self.history_y.pop(0)
            
            # Update plot
            self.line.set_data(self.history_x, self.history_y)
            
            # Sliding window X-limits
            if len(self.history_x) > 1:
                self.ax.set_xlim(self.history_x[0], self.history_x[-1])
            elif len(self.history_x) == 1:
                self.ax.set_xlim(self.history_x[0], self.history_x[0] + 1)
            
            # User adjustable Y-limits
            try:
                ymax = float(self.ymax_var.get())
                self.ax.set_ylim(-5, ymax) # Small buffer at bottom
            except:
                self.ax.relim()
                self.ax.autoscale_view(scalex=False, scaley=True)
                
            self.canvas.draw_idle()
        except:
            self.val_label.config(text="Error")

    def on_close(self):
        if self in self.gui.monitors:
            self.gui.monitors.remove(self)
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk(); app = OceanOpticsGUI(root); root.protocol("WM_DELETE_WINDOW", app.on_close); root.mainloop()

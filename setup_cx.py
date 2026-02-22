"""
cx_Freeze kurulum dosyasi - usb4000_gui.py
Kullanim: python setup_cx.py build
"""
import sys
import os
import tkinter
from cx_Freeze import setup, Executable

# Proje kök dizini
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Dahil edilecek ek dosya ve klasörler
include_files = [
    # oceandirect paketi (Python kaynak + DLL)
    (os.path.join(BASE_DIR, "oceandirect"), "oceandirect"),
    # Dil dosyalari
    (os.path.join(BASE_DIR, "languages"), "languages"),
    # Winusb suruculer (Sadece USB4000 için gerekli olanlar)
    (os.path.join(BASE_DIR, "winusb", "winusb_driver", "OOI_USB4000.inf"), os.path.join("winusb", "winusb_driver", "OOI_USB4000.inf")),
    (os.path.join(BASE_DIR, "winusb", "winusb_driver", "OOI_USB4000.cat"), os.path.join("winusb", "winusb_driver", "OOI_USB4000.cat")),
    (os.path.join(BASE_DIR, "winusb", "winusb_driver", "amd64"), os.path.join("winusb", "winusb_driver", "amd64")),
    (os.path.join(BASE_DIR, "winusb", "winusb_driver", "x86"), os.path.join("winusb", "winusb_driver", "x86")),
]

# Tcl/Tk dosyalarını bul ve dahil et (init.tcl hatası için)
tcl_dir = os.path.dirname(tkinter.__file__)
tk_dir  = os.path.join(os.path.dirname(tcl_dir))

# tkinter'in kullandığı Tcl/Tk veri dizinlerini bul
import _tkinter
tcl_version = _tkinter.TCL_VERSION   # örn. "8.6"
tk_version  = _tkinter.TK_VERSION

# Python'un lib klasöründen tcl8.6 ve tk8.6 dizinlerini bul
python_lib = os.path.join(os.path.dirname(sys.executable), "tcl")
if not os.path.isdir(python_lib):
    python_lib = os.path.join(os.path.dirname(sys.executable), "Lib")

# Standart Python kurulumunda Tcl/Tk verileri burada bulunur
tcl_data = os.path.join(os.path.dirname(sys.executable), "tcl", f"tcl{tcl_version}")
tk_data  = os.path.join(os.path.dirname(sys.executable), "tcl", f"tk{tk_version}")

if os.path.isdir(tcl_data):
    include_files.append((tcl_data, os.path.join("share", f"tcl{tcl_version}")))
if os.path.isdir(tk_data):
    include_files.append((tk_data,  os.path.join("share", f"tk{tk_version}")))

# config.json varsa ekle
config_path = os.path.join(BASE_DIR, "config.json")
if os.path.exists(config_path):
    include_files.append((config_path, "config.json"))

# data klasoru varsa ekle
data_path = os.path.join(BASE_DIR, "data")
if os.path.exists(data_path):
    include_files.append((data_path, "data"))

build_exe_options = {
    "packages": [
        "tkinter",
        "numpy",
        "matplotlib",
        "matplotlib.backends.backend_tkagg",
        "threading",
        "csv",
        "json",
        "subprocess",
    ],
    "excludes": ["PySide2", "PyQt5", "PyQt6", "IPython", "email", "html", "http", "pydoc", "test", "unittest", "xml", "notebook", "jedi"],
    "include_files": include_files,
    "include_msvcr": True,      # Visual C++ runtime dahil et
    "silent": True,
    # oceandirect klasörünü Python path'ine ekle (import için)
    "path": sys.path + [os.path.join(BASE_DIR, "oceandirect")],
}

# GUI uygulamasi - konsol penceresi yok (Windows)
base_gui = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="USB4000 Spektrometre",
    version="1.0.3",
    description="Ocean Optics USB4000 Spektrometre GUI",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="usb4000_gui.py",
            base=base_gui,
            target_name="USB4000_Spektrometre.exe",
            # icon="icon.ico",  # .ico dosyaniz varsa buraya ekleyin
        )
    ],
)

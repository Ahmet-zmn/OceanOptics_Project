import sys
import os

if getattr(sys, 'frozen', False):
    # sys._MEIPASS: PyInstaller'ın geçici dizini
    _BASE = sys._MEIPASS
    if _BASE not in sys.path:
        sys.path.insert(0, _BASE)
    
    # oceandirect klasörü için ekleme
    _OCEAN = os.path.join(_BASE, "oceandirect")
    if os.path.isdir(_OCEAN) and _OCEAN not in sys.path:
        sys.path.insert(0, _OCEAN)

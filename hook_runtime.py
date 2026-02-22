import sys
import os

# PyInstaller one-dir modunda sys._MEIPASS zaten sys.path'e eklenir
# ama oceandirect'in importlanabilmesi için açıkça ekliyoruz
if hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)

# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec dosyasi - usb4000_gui.py
#
# DÜZELTME: Python 3.10.0 + PyInstaller 6.11.0 kombinasyonunda
# oceandirect/OceanDirectAPI.py analiz edilirken "IndexError: tuple index out of range"
# hatası oluşuyordu. Çözüm: oceandirect'i Python paketi olarak analiz ettirmek
# yerine ham veri dosyası olarak kopyalatıp runtime hook ile sys.path'e ekliyoruz.

block_cipher = None

a = Analysis(
    ['usb4000_gui.py'],
    pathex=['.'],
    binaries=[
        # OceanDirect DLL dosyasini dahil et
        ('oceandirect\\lib\\OceanDirect.dll', 'oceandirect\\lib'),
    ],
    datas=[
        # oceandirect Python paketini analiz ETTIRMEDEN veri olarak kopyala
        ('oceandirect\\*.py',       'oceandirect'),
        ('oceandirect\\lib\\*',     'oceandirect\\lib'),
        # Dil dosyalari
        ('languages\\*.json',       'languages'),
        # Winusb suruculer
        ('winusb',                  'winusb'),
        # Konfigurasyonu dahil et (varsa)
        ('config.json',             '.'),
    ],
    hiddenimports=[
        # oceandirect buradan KALDIRILDI - veri olarak kopyalanıyor
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.colorchooser',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    # hook_runtime.py: sys._MEIPASS'ı sys.path'e ekler (oceandirect importu için)
    runtime_hooks=['hook_runtime.py'],
    # oceandirect analizi tamamen devre dışı
    excludes=['oceandirect'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='USB4000_Spektrometre',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI uygulamasi - konsol penceresi yok
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # .ico dosyaniz varsa buraya ekleyin: icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='USB4000_Spektrometre',
)

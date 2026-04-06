@echo off
REM ============================================
REM OceanOptics USB4000 Spectrometer Launcher
REM ============================================

cd /d "%~dp0"

REM Python'un PATH'te olup olmadığını kontrol et
where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pythonw "%~dp0OceanOptics_USB4000.py"
    exit /b 0
)

REM Varsayılan Python yollarını dene
if exist "C:\Program Files\Python310\pythonw.exe" (
    start "" "C:\Program Files\Python310\pythonw.exe" "%~dp0OceanOptics_USB4000.py"
    exit /b 0
)

if exist "C:\Program Files (x86)\Python310\pythonw.exe" (
    start "" "C:\Program Files (x86)\Python310\pythonw.exe" "%~dp0OceanOptics_USB4000.py"
    exit /b 0
)

REM Kullanici bazli Python kurulumu (Install for current user only)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe" "%~dp0OceanOptics_USB4000.py"
    exit /b 0
)

if exist "C:\Python310\pythonw.exe" (
    start "" "C:\Python310\pythonw.exe" "%~dp0OceanOptics_USB4000.py"
    exit /b 0
)

REM Python bulunamazsa hata göster
echo Python 3.10 bulunamadi!
echo Lütfen Python 3.10'u kurun veya PATH'e ekleyin.
pause


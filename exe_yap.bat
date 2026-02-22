@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
title USB4000 - Setup.exe Olusturucu

echo ============================================================
echo   OceanOptics USB4000 - Setup.exe Olusturucu
echo   (cx_Freeze + Inno Setup)
echo ============================================================
echo.

REM ─── 1. Python kontrolu ───────────────────────────────────
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen once kurulum.bat calistirin.
    pause & exit /b 1
)
echo [OK] Python:
python --version
echo.

REM ─── 2. cx_Freeze kontrolu ───────────────────────────────
echo [1/3] cx_Freeze kontrol ediliyor...
python -c "import cx_Freeze" > nul 2>&1
if %errorlevel% neq 0 (
    echo cx_Freeze kuruluyor...
    python -m pip install cx-freeze --quiet --no-warn-conflicts
    python -c "import cx_Freeze" > nul 2>&1
    if %errorlevel% neq 0 (
        echo [HATA] cx_Freeze kurulamadi!
        pause & exit /b 1
    )
)
echo [OK] cx_Freeze hazir.
echo.

REM ─── 3. Eski build temizle ───────────────────────────────
echo [2/3] Eski build temizleniyor...
if exist "build"  rmdir /s /q build
if exist "dist"   rmdir /s /q dist
echo [OK] Temizlendi.
echo.

REM ─── 4. cx_Freeze ile EXE olustur ───────────────────────
echo ============================================================
echo   [3/3] Uygulama derleniyor... (cx_Freeze)
echo ============================================================
echo.

python setup_cx.py build

if %errorlevel% neq 0 (
    echo.
    echo [HATA] Derleme basarisiz!
    pause & exit /b 1
)

REM Build klasor adini bul
for /d %%D in (build\exe.*) do set BUILD_DIR=%%D
echo [OK] Uygulama derlendi: %BUILD_DIR%
echo.

REM ─── 5. Inno Setup kuruluyor mu kontrol et ───────────────
echo ============================================================
echo   [4/4] Setup.exe olusturuluyor... (Inno Setup)
echo ============================================================
echo.

REM Inno Setup'i ara (tum olası kurulum yerleri)
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

REM PATH'ten de ara
if "%ISCC%"=="" (
    for %%X in (ISCC.exe) do set "ISCC=%%~$PATH:X"
)

if "%ISCC%"=="" (
    echo Inno Setup bulunamadi, winget ile kuruluyor...
    winget install --id JRSoftware.InnoSetup --silent --accept-source-agreements --accept-package-agreements
    REM winget "No upgrade" durumunda da hata kodu doner, gormezden gel
    REM PATH'i yenile
    for /f "tokens=*" %%i in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"PATH\",\"Machine\") + \";\" + [System.Environment]::GetEnvironmentVariable(\"PATH\",\"User\")"') do set PATH=%%i
    REM Tekrar ara
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo [HATA] Inno Setup hala bulunamadi!
    echo Lutfen https://jrsoftware.org/isdl.php adresinden kurun.
    pause & exit /b 1
)

echo [OK] Inno Setup: %ISCC%
echo.

REM ─── 6. setup.iss derle ──────────────────────────────────
mkdir dist > nul 2>&1

"%ISCC%" setup.iss

if %errorlevel% neq 0 (
    echo.
    echo [HATA] Setup.exe olusturma basarisiz!
    pause & exit /b 1
)

echo.
echo ============================================================
echo   BASARILI! Setup.exe olusturuldu:
echo   dist\OceanOptics_USB4000_Setup.exe
echo ============================================================
echo.

set /p ACMAK=dist klasorunu simdi ac? (E/H): 
if /i "!ACMAK!"=="E" explorer dist

pause

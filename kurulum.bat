@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
title OceanOptics Proje Kurulumu

echo ============================================================
echo   OceanOptics USB4000 Spektrometre - Kurulum
echo ============================================================
echo.

REM Python var mi kontrol et
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [UYARI] Python bulunamadi! Otomatik olarak yukleniyor...
    echo.

    REM Yerel kurulum dosyasi var mi kontrol et
    set PYTHON_INSTALLER=tools\python-3.10.0-amd64.exe
    if exist "%PYTHON_INSTALLER%" (
        echo Yerel kurulum dosyasi bulundu: %PYTHON_INSTALLER%
        echo Python kuruluyor... (Lutfen bekleyin)
        "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        if %errorlevel% neq 0 (
            echo [HATA] Yerel kurulum basarisiz oldu!
            pause
            exit /b 1
        )
        echo [OK] Python yerel dosyadan kuruldu.
    ) else (
        echo Yerel kurulum dosyasi bulunamadi, winget deneniyor...
        winget install --id Python.Python.3.10 --silent --accept-source-agreements --accept-package-agreements
        if %errorlevel% neq 0 (
            echo [HATA] Python kurulamadi!
            echo Cozum: tools\ klasorune python-3.10.0-amd64.exe dosyasini koyun.
            echo Indirme: https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe
            pause
            exit /b 1
        )
        echo [OK] Python winget ile kuruldu.
    )

    REM PATH'i yenile (bu oturumda gecerli olsun)
    for /f "tokens=*" %%i in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"PATH\",\"Machine\") + \";\" + [System.Environment]::GetEnvironmentVariable(\"PATH\",\"User\")"') do set PATH=%%i

    REM Tekrar kontrol et
    python --version > nul 2>&1
    if %errorlevel% neq 0 (
        echo [HATA] Python kuruldu ancak PATH henuz guncellenmedi.
        echo Lutfen bu bat dosyasini kapatip yeniden calistirin.
        pause
        exit /b 1
    )
    echo [OK] Python basariyla kuruldu.
) else (
    echo [OK] Python bulundu:
    python --version
)
echo.

REM pip'yi guncelle
echo [1/6] pip guncelleniyor...
python -m pip install --upgrade pip --quiet
echo [OK] pip guncellendi.
echo.

REM ---- Kutuphaneleri kontrol et, yoksa kur ----

REM numpy
echo [2/6] numpy kontrol ediliyor...
python -c "import numpy" > nul 2>&1
if %errorlevel% neq 0 (
    echo   numpy bulunamadi, kuruluyor...
    python -m pip install numpy --quiet
    if %errorlevel% neq 0 (
        echo [HATA] numpy kurulamadi!
        pause
        exit /b 1
    )
    echo [OK] numpy kuruldu.
) else (
    echo [OK] numpy zaten yuklu.
)
echo.

REM matplotlib
echo [3/6] matplotlib kontrol ediliyor...
python -c "import matplotlib" > nul 2>&1
if %errorlevel% neq 0 (
    echo   matplotlib bulunamadi, kuruluyor...
    python -m pip install matplotlib --quiet
    if %errorlevel% neq 0 (
        echo [HATA] matplotlib kurulamadi!
        pause
        exit /b 1
    )
    echo [OK] matplotlib kuruldu.
) else (
    echo [OK] matplotlib zaten yuklu.
)
echo.

REM cx_Freeze
echo [4/6] cx_Freeze kontrol ediliyor...
python -c "import cx_Freeze" > nul 2>&1
if %errorlevel% neq 0 (
    echo   cx_Freeze bulunamadi, kuruluyor...
    python -m pip install cx-freeze --quiet --no-warn-conflicts
    python -c "import cx_Freeze" > nul 2>&1
    if %errorlevel% neq 0 (
        echo [HATA] cx_Freeze kurulamadi!
        pause
        exit /b 1
    )
    echo [OK] cx_Freeze kuruldu.
) else (
    echo [OK] cx_Freeze zaten yuklu.
)
echo.

REM Gerekli klasorleri olustur
echo [5/6] Klasor yapisi kontrol ediliyor...
if not exist "data" (
    mkdir data
    echo [OK] 'data' klasoru olusturuldu.
) else (
    echo [OK] 'data' klasoru mevcut.
)
if not exist "languages" (
    mkdir languages
    echo [OK] 'languages' klasoru olusturuldu.
) else (
    echo [OK] 'languages' klasoru mevcut.
)

REM oceandirect klasoru var mi kontrol et
if not exist "oceandirect" (
    echo [UYARI] 'oceandirect' klasoru bulunamadi!
    echo   Lutfen OceanDirect SDK klasorunu proje dizinine kopyalayin.
) else (
    echo [OK] 'oceandirect' SDK klasoru mevcut.
)

REM winusb klasoru var mi kontrol et
if not exist "winusb" (
    echo [UYARI] 'winusb' klasoru bulunamadi!
    echo   Suruculer icin 'winusb' klasorunu proje dizinine kopyalayin.
) else (
    echo [OK] 'winusb' surucu klasoru mevcut.
)
echo.

REM OmniDriver SDK kurulumu
echo [6/6] OmniDriver SDK kontrol ediliyor...
set OMNI_INSTALLER=winusb\OmniDriver-2.80-win64-installer.exe
if exist "%OMNI_INSTALLER%" (
    set /p SDK_CEVAP=OmniDriver 2.80 SDK kurulsun mu? (E/H): 
    if /i "!SDK_CEVAP!"=="E" (
        echo OmniDriver SDK yukleniyor... (Yonetici izni gerekebilir)
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%CD%\%OMNI_INSTALLER%' -Verb RunAs -Wait"
        echo [OK] OmniDriver SDK kurulumu tamamlandi.
    ) else (
        echo [ATLANDI] OmniDriver SDK kurulumu atlandi.
    )
) else (
    echo [UYARI] OmniDriver kurulum dosyasi bulunamadi: %OMNI_INSTALLER%
)
echo.

echo ============================================================
echo   Kurulum tamamlandi!
echo ============================================================
echo.
echo   Yuklenen / kontrol edilen kutuphaneler:
echo     - numpy
echo     - matplotlib
echo     - cx_Freeze
echo ============================================================
echo.

set /p CEVAP=Uygulamayi simdi baslatmak ister misiniz? (E/H): 
if /i "%CEVAP%"=="E" (
    echo.
    echo Uygulama baslatiliyor...
    python usb4000_gui.py
) else (
    echo.
    echo Uygulamayi baslatmak icin: python usb4000_gui.py
)

pause

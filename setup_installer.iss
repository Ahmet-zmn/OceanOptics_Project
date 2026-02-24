; ============================================================================
; OceanOptics USB4000 Spectrometer - Offline Installer
; Inno Setup Script
; 
; Bu installer internetsiz ortamlarda calisir:
;   - Python 3.10 kontrol edilir, yoksa sessiz kurulur
;   - Pip kutuphaneleri kontrol edilir, eksikler offline kurulur
;   - OmniDriver opsiyonel olarak kurulur
;   - Kurulum dizinine okuma/yazma yetkileri verilir
;   - Masaustu kisayolu olusturulur
; ============================================================================

#define MyAppName "OceanOptics USB4000 Spectrometer"
#define MyAppVersion "1.0.6"
#define MyAppPublisher "Ahmet OZMEN"
#define MyAppURL "https://github.com/Ahmet-zmn/OceanOptics_Project"
#define MyAppExeName "launch_app.bat"

[Setup]
AppId={{A3F8E2D0-1B2C-4D5E-6F7A-8B9C0D1E2F3A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\OceanOptics_USB4000
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=OceanOptics_USB4000_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Components]
Name: "main"; Description: "Uygulama dosyalari"; Types: full compact custom; Flags: fixed
Name: "omnidriver"; Description: "OmniDriver 2.80 (USB4000 surucusu)"; Types: full

[Files]
; ---- Visual C++ Redistributable ----
Source: "tools\VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; ---- Python 3.10 Installer ----
Source: "tools\python-3.10.0-amd64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; ---- OmniDriver Installer ----
Source: "tools\OmniDriver-2.80-win64-installer.exe"; DestDir: "{tmp}"; Components: omnidriver; Flags: deleteafterinstall

; ---- Offline Pip Packages ----
Source: "offline_packages\*.whl"; DestDir: "{app}\offline_packages"; Flags: ignoreversion

; ---- Application Files ----
Source: "usb4000_gui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
Source: "version.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "launch_app.bat"; DestDir: "{app}"; Flags: ignoreversion

; ---- OceanDirect SDK ----
Source: "oceandirect\*.py"; DestDir: "{app}\oceandirect"; Flags: ignoreversion
Source: "oceandirect\lib\*"; DestDir: "{app}\oceandirect\lib"; Flags: ignoreversion recursesubdirs

; ---- Language Files ----
Source: "languages\*.json"; DestDir: "{app}\languages"; Flags: ignoreversion

; ---- WinUSB Drivers ----
Source: "winusb\*"; DestDir: "{app}\winusb"; Flags: ignoreversion recursesubdirs

[Dirs]
; Kurulum dizinine ve alt klasorlere tam okuma/yazma yetkisi ver (Everyone)
Name: "{app}"; Permissions: users-full
Name: "{app}\data"; Permissions: users-full
Name: "{app}\languages"; Permissions: users-full
Name: "{app}\oceandirect"; Permissions: users-full
Name: "{app}\oceandirect\lib"; Permissions: users-full
Name: "{app}\winusb"; Permissions: users-full
Name: "{app}\offline_packages"; Permissions: users-full

[Icons]
; Masaustu kisayolu
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 14
; Baslat menusu kisayolu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 14
Name: "{group}\Kaldir {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; ---- OmniDriver Kurulumu (opsiyonel - kullanici secerse) ----
Filename: "{tmp}\OmniDriver-2.80-win64-installer.exe"; StatusMsg: "OmniDriver 2.80 kuruluyor..."; Components: omnidriver; Flags: waituntilterminated

; ---- Kurulum sonrasi uygulamayi calistir ----
Filename: "{app}\{#MyAppExeName}"; Description: "OceanOptics USB4000 uygulamasini baslat"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent shellexec

[Code]

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  BatFile: String;
  BatContent: TStringList;
  AppDir, TmpDir, PythonInstaller, VCRedist, OfflinePkgDir, LogFile: String;
  PythonExe: String;
  LogContent: TStringList;
begin
  if CurStep = ssPostInstall then
  begin
    // Yollari hazirla
    AppDir := ExpandConstant('{app}');
    TmpDir := ExpandConstant('{tmp}');
    PythonInstaller := TmpDir + '\python-3.10.0-amd64.exe';
    VCRedist := TmpDir + '\VC_redist.x64.exe';
    OfflinePkgDir := AppDir + '\offline_packages';
    LogFile := AppDir + '\kurulum_raporu.txt';
    BatFile := TmpDir + '\install_deps.bat';

    // data klasorunu olustur
    ForceDirectories(AppDir + '\data');

    // ---- Log dosyasi basla ----
    LogContent := TStringList.Create;
    try
      LogContent.Add('============================================================');
      LogContent.Add('  OceanOptics USB4000 Spectrometer - Kurulum Raporu');
      LogContent.Add('============================================================');
      LogContent.Add('Kurulum Dizini: ' + AppDir);
      LogContent.Add('------------------------------------------------------------');
      LogContent.Add('');

      // ============================================
      // ADIM 1: Visual C++ Redistributable (Exec)
      // ============================================
      Log('ADIM 1: Visual C++ Redistributable kuruluyor...');
      LogContent.Add('[ADIM 1/4] Visual C++ Redistributable');

      if FileExists(VCRedist) then
      begin
        Exec(VCRedist, '/install /quiet /norestart', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        if (ResultCode = 0) or (ResultCode = 1638) or (ResultCode = 3010) then
        begin
          Log('VC++ kurulumu basarili. Kod: ' + IntToStr(ResultCode));
          LogContent.Add('  [BASARILI] Visual C++ Redistributable kuruldu.');
        end
        else
        begin
          Log('VC++ kurulumu hata: ' + IntToStr(ResultCode));
          LogContent.Add('  [HATA] VC++ kurulumu basarisiz! Hata kodu: ' + IntToStr(ResultCode));
        end;
      end
      else
      begin
        Log('VC++ dosyasi bulunamadi: ' + VCRedist);
        LogContent.Add('  [UYARI] VC++ dosyasi bulunamadi, atlaniyor.');
      end;

      // ============================================
      // ADIM 2: Python 3.10 (Exec)
      // ============================================
      Log('ADIM 2: Python 3.10 kontrol ediliyor...');
      LogContent.Add('');
      LogContent.Add('[ADIM 2/4] Python 3.10');

      // Python 3.10 bilinen yollardan kontrol et
      PythonExe := '';
      if FileExists('C:\Program Files\Python310\python.exe') then
        PythonExe := 'C:\Program Files\Python310\python.exe'
      else if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python310\python.exe')) then
        PythonExe := ExpandConstant('{localappdata}\Programs\Python\Python310\python.exe')
      else if FileExists('C:\Python310\python.exe') then
        PythonExe := 'C:\Python310\python.exe'
      else if FileExists('C:\Program Files (x86)\Python310\python.exe') then
        PythonExe := 'C:\Program Files (x86)\Python310\python.exe';

      if PythonExe <> '' then
      begin
        Log('Python 3.10 zaten kurulu: ' + PythonExe);
        LogContent.Add('  [BASARILI] Python 3.10 zaten kurulu: ' + PythonExe);
      end
      else
      begin
        // Python kur
        Log('Python 3.10 bulunamadi, kuruluyor...');
        LogContent.Add('  [ISLEM] Python 3.10 bulunamadi, kuruluyor...');

        if FileExists(PythonInstaller) then
        begin
          Exec(PythonInstaller, '/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
          if ResultCode = 0 then
          begin
            Log('Python 3.10 basariyla kuruldu.');
            LogContent.Add('  [BASARILI] Python 3.10 basariyla kuruldu.');
          end
          else
          begin
            Log('Python 3.10 kurulumu hata: ' + IntToStr(ResultCode));
            LogContent.Add('  [HATA] Python 3.10 kurulumu basarisiz! Hata kodu: ' + IntToStr(ResultCode));
          end;
        end
        else
        begin
          Log('Python installer bulunamadi: ' + PythonInstaller);
          LogContent.Add('  [HATA] Python installer dosyasi bulunamadi!');
        end;

        // Kurulumdan sonra PythonExe yolunu belirle
        if FileExists('C:\Program Files\Python310\python.exe') then
          PythonExe := 'C:\Program Files\Python310\python.exe'
        else if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python310\python.exe')) then
          PythonExe := ExpandConstant('{localappdata}\Programs\Python\Python310\python.exe');
      end;

      // Python bulunamazsa hata ver ve pip atla
      if (PythonExe = '') or (not FileExists(PythonExe)) then
      begin
        Log('Python exe bulunamadi, pip kurulumu atlanacak.');
        LogContent.Add('  [HATA] Python bulunamadi, kutuphane kurulumu atlanacak.');
        LogContent.Add('');
        LogContent.Add('[ADIM 3/4] Kutuphane Kurulumu');
        LogContent.Add('  [ATLANDI] Python bulunamadi.');
        LogContent.Add('');
        LogContent.Add('[ADIM 4/4] Dosya Izinleri');
        // Dosya izinlerini yine de ayarla
        Exec('cmd.exe', '/C icacls "' + AppDir + '" /grant Users:(OI)(CI)F /T /Q', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        if ResultCode = 0 then
          LogContent.Add('  [BASARILI] Dosya izinleri ayarlandi.')
        else
          LogContent.Add('  [HATA] Dosya izinleri ayarlanamadi.');
        LogContent.Add('');
        LogContent.Add('------------------------------------------------------------');
        LogContent.Add('SONUC: KURULUM HATALI - Python bulunamadi!');
        LogContent.Add('------------------------------------------------------------');
        LogContent.SaveToFile(LogFile);
        LogContent.Free;
        MsgBox('Python 3.10 kurulamadi. Lutfen manuel olarak kurun.' + #13#10 + 'Detaylar: ' + LogFile, mbError, MB_OK);
        Exit;
      end;

      LogContent.Add('  [BILGI] Python yolu: ' + PythonExe);

      // ============================================
      // ADIM 3: Pip kutuphaneleri (Batch Script)
      // ============================================
      LogContent.Add('');
      LogContent.Add('[ADIM 3/4] Python Kutuphaneleri');

      // Bat script sadece pip kurulumu icin
      BatContent := TStringList.Create;
      try
        BatContent.Add('@echo off');
        BatContent.Add('setlocal EnableDelayedExpansion');
        BatContent.Add('chcp 65001 >nul 2>&1');
        BatContent.Add('title OceanOptics USB4000 - Kutuphane Kurulumu');
        BatContent.Add('color 0A');
        BatContent.Add('');
        BatContent.Add('set "PYTHON_EXE=' + PythonExe + '"');
        BatContent.Add('set "PKGDIR=' + OfflinePkgDir + '"');
        BatContent.Add('set "LOGFILE=' + LogFile + '"');
        BatContent.Add('set "ERRORS=0"');
        BatContent.Add('');
        BatContent.Add('echo ============================================================');
        BatContent.Add('echo   Python Kutuphane Kurulumu Baslatildi');
        BatContent.Add('echo   Python: %PYTHON_EXE%');
        BatContent.Add('echo ============================================================');
        BatContent.Add('echo.');
        BatContent.Add('');

        // Her paket tek tek - duz yapi, ic ice blok yok
        BatContent.Add('echo [1/11] numpy kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" numpy >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] numpy kuruldu. ) else ( echo   [HATA] numpy BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [2/11] matplotlib kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" matplotlib >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] matplotlib kuruldu. ) else ( echo   [HATA] matplotlib BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [3/11] pillow kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" pillow >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] pillow kuruldu. ) else ( echo   [HATA] pillow BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [4/11] contourpy kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" contourpy >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] contourpy kuruldu. ) else ( echo   [HATA] contourpy BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [5/11] cycler kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" cycler >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] cycler kuruldu. ) else ( echo   [HATA] cycler BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [6/11] fonttools kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" fonttools >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] fonttools kuruldu. ) else ( echo   [HATA] fonttools BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [7/11] kiwisolver kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" kiwisolver >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] kiwisolver kuruldu. ) else ( echo   [HATA] kiwisolver BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [8/11] packaging kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" packaging >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] packaging kuruldu. ) else ( echo   [HATA] packaging BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [9/11] pyparsing kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" pyparsing >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] pyparsing kuruldu. ) else ( echo   [HATA] pyparsing BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [10/11] python-dateutil kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" python-dateutil >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] python-dateutil kuruldu. ) else ( echo   [HATA] python-dateutil BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('echo [11/11] six kuruluyor...');
        BatContent.Add('"%PYTHON_EXE%" -m pip install --no-index --find-links="%PKGDIR%" six >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] six kuruldu. ) else ( echo   [HATA] six BASARISIZ! & set /a ERRORS+=1 )');

        BatContent.Add('');
        BatContent.Add('echo.');
        BatContent.Add('echo ============================================================');

        // Dosya izinleri
        BatContent.Add('echo [ADIM 4/4] Dosya izinleri ayarlaniyor...');
        BatContent.Add('icacls "' + AppDir + '" /grant Users:(OI)(CI)F /T /Q >nul 2>&1');
        BatContent.Add('if !ERRORLEVEL! equ 0 ( echo   [BASARILI] Dosya izinleri ayarlandi. ) else ( echo   [HATA] Izinler ayarlanamadi! & set /a ERRORS+=1 )');

        BatContent.Add('');
        BatContent.Add('echo.');
        BatContent.Add('echo ============================================================');
        BatContent.Add('if !ERRORS! equ 0 (');
        BatContent.Add('    echo   KURULUM TAMAMLANDI - Tum adimlar basarili!');
        BatContent.Add(') else (');
        BatContent.Add('    echo   KURULUM TAMAMLANDI - !ERRORS! adet hata olustu!');
        BatContent.Add(')');
        BatContent.Add('echo ============================================================');
        BatContent.Add('echo.');
        BatContent.Add('echo Bu pencere 10 saniye icinde kapanacak...');
        BatContent.Add('timeout /t 10 /nobreak >nul');
        BatContent.Add('exit /b !ERRORS!');

        // Bat dosyasini kaydet
        BatContent.SaveToFile(BatFile);
      finally
        BatContent.Free;
      end;

      // ---- Bat dosyasini GORUNUR pencerede calistir ----
      Log('Pip install bat calistiriliyor...');
      Exec('cmd.exe', '/C "' + BatFile + '"',
        AppDir, SW_SHOW, ewWaitUntilTerminated, ResultCode);

      // Sonuclari log dosyasina ekle
      if ResultCode = 0 then
      begin
        LogContent.Add('  [BASARILI] Tum kutuphaneler kuruldu.');
        Log('Pip kurulumu basarili.');
      end
      else
      begin
        LogContent.Add('  [UYARI] Kutuphane kurulumunda ' + IntToStr(ResultCode) + ' hata olustu.');
        Log('Pip kurulumu hata: ' + IntToStr(ResultCode));
      end;

      // Dosya izinleri sonucu
      LogContent.Add('');
      LogContent.Add('[ADIM 4/4] Dosya Izinleri');
      LogContent.Add('  [BASARILI] Dosya izinleri ayarlandi.');

      // ---- Final log ----
      LogContent.Add('');
      LogContent.Add('------------------------------------------------------------');
      if ResultCode = 0 then
        LogContent.Add('SONUC: KURULUM BASARILI - Tum adimlar tamamlandi.')
      else
        LogContent.Add('SONUC: KURULUM TAMAMLANDI - Bazi hatalalar olustu.');
      LogContent.Add('------------------------------------------------------------');

      LogContent.SaveToFile(LogFile);
    finally
      LogContent.Free;
    end;
  end;
end;

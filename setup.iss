; ============================================================
; OceanOptics USB4000 Spektrometre - Inno Setup Script
; ============================================================

#define MyAppName      "OceanOptics USB4000 Spektrometre"
#define MyAppVersion   "1.0.2"
#define MyAppPublisher "OceanOptics"
#define MyAppExeName   "USB4000_Spektrometre.exe"
#define MyAppDir       "build\exe.win-amd64-3.10"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://www.oceanoptics.com
DefaultDirName={autopf}\OceanOptics_USB4000
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=OceanOptics_USB4000_Setup
SetupIconFile=
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=
WizardImageFile=
MinVersion=6.1

[Languages]
Name: "turkish";  MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english";  MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";   Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek görevler:"
Name: "startmenuicon"; Description: "Başlangıç menüsüne ekle";    GroupDescription: "Ek görevler:"

[Files]
; Ana EXE ve DLL'ler
Source: "{#MyAppDir}\{#MyAppExeName}";   DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDir}\*.dll";             DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDir}\*.txt";             DestDir: "{app}"; Flags: ignoreversion

; Lib klasörü
Source: "{#MyAppDir}\lib\*"; DestDir: "{app}\lib"; Flags: ignoreversion recursesubdirs createallsubdirs

; Dil dosyaları
Source: "{#MyAppDir}\languages\*"; DestDir: "{app}\languages"; Flags: ignoreversion recursesubdirs createallsubdirs

; Share klasörü (Tcl/Tk init.tcl buradadır — zorunlu!)
Source: "{#MyAppDir}\share\*"; DestDir: "{app}\share"; Flags: ignoreversion recursesubdirs createallsubdirs

; OceanDirect SDK
Source: "{#MyAppDir}\oceandirect\*"; DestDir: "{app}\oceandirect"; Flags: ignoreversion recursesubdirs createallsubdirs

; WinUSB (Slim subset for USB4000)
Source: "{#MyAppDir}\winusb\*"; DestDir: "{app}\winusb"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Ana kurulum klasörüne yazma izni ver (config.json için)
Name: "{app}"; Permissions: users-modify
; data klasörünü oluştur ve yazma izni ver (kayıt dosyaları için)
Name: "{app}\data"; Permissions: users-full
; winusb klasörünü oluştur
Name: "{app}\winusb"; Permissions: users-full

[Icons]
; Başlangıç menüsü
Name: "{group}\{#MyAppName}";           Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon
Name: "{group}\Kaldır ({#MyAppName})";  Filename: "{uninstallexe}";        Tasks: startmenuicon

; Masaüstü kısayolu
Name: "{autodesktop}\{#MyAppName}";     Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Tüm kullanıcılara tam yazma izni ver (icacls ile ek güvence)
Filename: "icacls.exe"; \
    Parameters: """{app}""  /grant *S-1-5-32-545:(OI)(CI)F /T /Q"; \
    Flags: runhidden waituntilterminated; StatusMsg: "Klasör izinleri ayarlanıyor..."

; OmniDriver İndirme ve Kurulum (Opsiyonel/Setup sırasında indirilir)
; Kullanıcı interneti yoksa hata alabilir, bu yüzden bu adımı dikkatli kullanıyoruz
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$json=(iwr -Uri 'https://raw.githubusercontent.com/Ahmet-zmn/OceanOptics_Project/main/version.json' -UseBasicParsing | ConvertFrom-Json); $url=$json.omni_driver_url; $out='{app}\winusb\OmniDriver-2.80-win64-installer.exe'; if(!(Test-Path $out)){ Write-Host ""İndiriliyor: $url""; iwr -Uri $url -OutFile $out }"""; \
    Flags: runhidden waituntilterminated; StatusMsg: "OmniDriver (USB Sürücüleri) GitHub'dan indiriliyor, lütfen bekleyin..."; \
    Check: not FileExists(ExpandConstant('{app}\winusb\OmniDriver-2.80-win64-installer.exe'))

; OmniDriver Çalıştırma
Filename: "{app}\winusb\OmniDriver-2.80-win64-installer.exe"; \
    Description: "OmniDriver Sürücülerini Kur"; \
    Flags: postinstall skipifsilent; Check: FileExists(ExpandConstant('{app}\winusb\OmniDriver-2.80-win64-installer.exe'))

Filename: "{app}\{#MyAppExeName}"; \
    Description: "Uygulamayı şimdi başlat"; \
    Flags: nowait postinstall skipifsilent runasoriginaluser

[UninstallDelete]
; Kullanıcı verilerini silme (sadece program dosyaları silinsin)
Type: filesandordirs; Name: "{app}\lib"
Type: filesandordirs; Name: "{app}\share"

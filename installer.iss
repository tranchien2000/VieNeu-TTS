; VieNeu-TTS Installer Script for Inno Setup
; https://jrsoftware.org/isinfo.php

#define MyAppName "VieNeu-TTS"
#define MyAppVersion "2.5.0"
#define MyAppPublisher "Pham Nguyen Ngoc Bao"
#define MyAppURL "https://github.com/pnnbao97/VieNeu-TTS"
#define MyAppExeName "VieNeu-TTS.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{VieNeu-TTS-2024}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer_output
OutputBaseFilename=VieNeu-TTS-Setup-{#MyAppVersion}
SetupIconFile=docs\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Tu dong chay khi khoi dong Windows"; GroupDescription: "Tuy chon khac:"; Flags: unchecked

[Files]
; Python Embedded (download separately)
Source: "python-embed\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs
; VieNeu-TTS Source
Source: "src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "apps\*"; DestDir: "{app}\apps"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "examples\*"; DestDir: "{app}\examples"; Flags: ignoreversion recursesubdirs createallsubdirs
; Config files
Source: "config.yaml"; DestDir: "{app}"; Flags: ignoreversion
Source: "pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "uv.lock"; DestDir: "{app}"; Flags: ignoreversion
; Scripts
Source: "run_server_persistent.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "run_server_silent.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup_autostart.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "remove_autostart.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "check_cache.bat"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUICKSTART.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
; Pre-downloaded models (optional - comment out if too large)
; Source: "models\*"; DestDir: "{userappdata}\huggingface\hub"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\run_server_persistent.bat"; IconFilename: "{app}\docs\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\run_server_persistent.bat"; IconFilename: "{app}\docs\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\run_server_persistent.bat"; Description: "Chay VieNeu-TTS ngay"; Flags: nowait postinstall skipifsilent shellexec

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Setup auto-start if selected
    if IsTaskSelected('autostart') then
    begin
      Exec(ExpandConstant('{app}\setup_autostart.bat'), '1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;

[UninstallRun]
Filename: "{app}\remove_autostart.bat"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

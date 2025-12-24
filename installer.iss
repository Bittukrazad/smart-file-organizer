; ============================================
; FILE: installer.iss
; Inno Setup installer script
; ============================================

; Smart File Organizer Pro Installer Script
; Requires Inno Setup 6.0 or later

#define MyAppName "Smart File Organizer Pro"
#define MyAppVersion GetEnv("APP_VERSION")   ; 🔒 Single source of truth
#define MyAppPublisher "BITTU KUMAR AZAD"
#define MyAppURL "https://github.com/Bittukrazad/smart-file-organizer"
#define MyAppExeName "SmartFileOrganizer.exe"
#define MyAppId "{{8F9E6C1A-2B3D-4E5F-6A7B-8C9D0E1F2A3B}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

OutputDir=release
OutputBaseFilename=SmartFileOrganizer_Setup_v{#MyAppVersion}

SetupIconFile=app\resources\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCopyright=Copyright (C) 2025 {#MyAppPublisher}

MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64


[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"


[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

Name: "startup"; Description: "Launch at Windows startup"; \
    GroupDescription: "Other options:"; Flags: unchecked


[Files]
; Copy entire PyInstaller output folder
Source: "dist\SmartFileOrganizer\*"; \
    DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs


[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup


[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent


[Code]

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RegWriteStringValue(
      HKCU,
      'Software\Classes\AppUserModelId\fileorgpro.smart_file_organizer',
      'DisplayName',
      '{#MyAppName}'
    );
  end;
end;

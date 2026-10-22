; Compile with Inno Setup 6.2.2; see LEGACY.md.
#ifndef AppVersion
  #error AppVersion must be supplied from VERSION using /DAppVersion
#endif

[Setup]
; A separate stable identity keeps Legacy and the modern edition independent.
AppId={{25E3D1C8-280E-4435-ADDD-AB717FF20F57}
AppName=Τρίλιζα Legacy
AppVersion={#AppVersion}
AppVerName=Τρίλιζα Legacy {#AppVersion}
DefaultDirName={localappdata}\Programs\TrilizaLegacy
UsePreviousAppDir=yes
DefaultGroupName=Τρίλιζα Legacy
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=6.1sp1
OutputDir=..\dist-legacy
OutputBaseFilename=Triliza-{#AppVersion}-Windows7-SP1-x64-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app.ico
DisableWelcomePage=no
UninstallDisplayIcon={app}\TrilizaLegacy.exe
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
VersionInfoVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist-legacy\TrilizaLegacy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Τρίλιζα Legacy"; Filename: "{app}\TrilizaLegacy.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Τρίλιζα Legacy"; Filename: "{app}\TrilizaLegacy.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\TrilizaLegacy.exe"; Description: "Launch Τρίλιζα Legacy"; Flags: nowait postinstall skipifsilent

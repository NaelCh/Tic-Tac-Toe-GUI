; Build from the repository root with:
; ISCC.exe /DAppVersion=1.3.3 installer\windows.iss
; AppVersion is supplied from VERSION by the release workflow.
#ifndef AppVersion
  #error AppVersion must be supplied from VERSION using /DAppVersion
#endif

[Setup]
; Keep this GUID stable so future versions upgrade the same application.
AppId={{72E520F5-29DC-4D60-8791-C85A53901B95}
AppName=Τρίλιζα
AppVersion={#AppVersion}
AppVerName=Τρίλιζα {#AppVersion}
DefaultDirName={localappdata}\Programs\Triliza
UsePreviousAppDir=yes
DefaultGroupName=Τρίλιζα
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=Triliza-{#AppVersion}-Windows-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app.ico
DisableWelcomePage=no
UninstallDisplayIcon={app}\Triliza.exe
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
VersionInfoVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\Triliza\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Τρίλιζα"; Filename: "{app}\Triliza.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Τρίλιζα"; Filename: "{app}\Triliza.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Triliza.exe"; Description: "Launch Τρίλιζα"; Flags: nowait postinstall skipifsilent

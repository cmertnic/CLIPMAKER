!include "MUI2.nsh"

Name "AI Video Clipper"
OutFile "AI_Video_Clipper_Setup.exe"
InstallDir "$PROGRAMFILES\AI Video Clipper"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Russian"

Section "Main"
    SetOutPath "$INSTDIR"
    File "dist\AI_Video_Clipper.exe"
    File "requirements.txt"
    File "README.txt"
    
    CreateDirectory "$SMPROGRAMS\AI Video Clipper"
    CreateShortCut "$SMPROGRAMS\AI Video Clipper\AI Video Clipper.lnk" "$INSTDIR\AI_Video_Clipper.exe"
    CreateShortCut "$DESKTOP\AI Video Clipper.lnk" "$INSTDIR\AI_Video_Clipper.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\AI_Video_Clipper.exe"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\README.txt"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\AI Video Clipper\AI Video Clipper.lnk"
    RMDir "$SMPROGRAMS\AI Video Clipper"
    Delete "$DESKTOP\AI Video Clipper.lnk"
SectionEnd
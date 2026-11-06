# Copyright (c) 2022 UltiMaker B.V.
# Cura's build system is released under the terms of the AGPLv3 or higher.

!define APP_NAME "BCN3D Stratos 2.3.0."
!define COMP_NAME "BCN3D"
!define WEB_SITE ""
!define VERSION "2.3.0"
!define VIVERSION "2.3.0.0"
!define COPYRIGHT "Copyright (c) 2026 BCN3D"
!define DESCRIPTION "Application"
!define LICENSE_TXT "C:\Users\Enric\Stratos-2\packaging\NSIS\..\..\packaging\cura_license.txt"
!define INSTALLER_NAME "BCN3D_Stratos-2.3.0.exe"
!define MAIN_APP_EXE "BCN3D-Stratos.exe"
!define INSTALL_TYPE "SetShellVarContext all"
!define REG_ROOT "HKLM"
!define REG_APP_PATH "Software\Microsoft\Windows\CurrentVersion\App Paths\${APP_NAME}-${VERSION}"
!define UNINSTALL_PATH "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}-${VERSION}"

!define REG_START_MENU "Start Menu Folder"

;Require administrator access
RequestExecutionLevel admin

var SM_Folder

######################################################################

VIProductVersion  "${VIVERSION}"
VIAddVersionKey "ProductName"  "BCN3D Stratos"
VIAddVersionKey "CompanyName"  "${COMP_NAME}"
VIAddVersionKey "LegalCopyright"  "${COPYRIGHT}"
VIAddVersionKey "FileDescription"  "${DESCRIPTION}"
VIAddVersionKey "FileVersion"  "${VIVERSION}"

######################################################################

SetCompressor LZMA
Name "${APP_NAME}"
Caption "${APP_NAME}"
OutFile "${INSTALLER_NAME}"
BrandingText "${APP_NAME}"
InstallDir "$PROGRAMFILES64\${APP_NAME}"

######################################################################

!include "MUI2.nsh"
!include fileassoc.nsh

!define MUI_ABORTWARNING
!define MUI_UNABORTWARNING

!define MUI_ICON "C:\Users\Enric\Stratos-2\packaging\NSIS\..\..\packaging\icons\Cura.ico"

!define MUI_WELCOMEFINISHPAGE_BITMAP "C:\Users\Enric\Stratos-2\packaging\NSIS\..\..\packaging\NSIS\cura_banner_nsis.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "C:\Users\Enric\Stratos-2\packaging\NSIS\..\..\packaging\NSIS\cura_banner_nsis.bmp"

!insertmacro MUI_PAGE_WELCOME

!ifdef LICENSE_TXT
!insertmacro MUI_PAGE_LICENSE "${LICENSE_TXT}"
!endif

!insertmacro MUI_PAGE_DIRECTORY

!ifdef REG_START_MENU
!define MUI_STARTMENUPAGE_NODISABLE
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "BCN3D Stratos"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "${REG_ROOT}"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${UNINSTALL_PATH}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "${REG_START_MENU}"
!insertmacro MUI_PAGE_STARTMENU Application $SM_Folder
!endif

!insertmacro MUI_PAGE_INSTFILES

# Set up explorer to run Cura instead of directly, so it's not executed elevated (with all negative consequences that brings for an unelevated user).
Function finishpageaction
CreateShortcut "$desktop\BCN3D-Stratos.lnk" "$instdir\BCN3D-Stratos.exe"
FunctionEnd

!define MUI_FINISHPAGE_RUN "$WINDIR\explorer.exe"
!define MUI_FINISHPAGE_RUN_PARAMETERS "$INSTDIR\${MAIN_APP_EXE}"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION finishpageaction
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM

!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

######################################################################

Section -MainProgram
${INSTALL_TYPE}
SetOverwrite ifnewer
SectionEnd

######################################################################

Section -Extension_Reg
!insertmacro APP_ASSOCIATE "stl" "Cura.model" "Standard Tessellation Language (STL) files" "$INSTDIR\${MAIN_APP_EXE},0" "Open with BCN3D Stratos " "$INSTDIR\${MAIN_APP_EXE} $\"%1$\""
!insertmacro APP_ASSOCIATE "3mf" "Cura.project" "3D Manufacturing Format (3MF) files" "$INSTDIR\${MAIN_APP_EXE},0" "Open with BCN3D Stratos " "$INSTDIR\${MAIN_APP_EXE} $\"%1$\""
SectionEnd

Section -Icons_Reg
SetOutPath "$INSTDIR"
File /r "C:\Users\Enric\Stratos-2\dist\BCN3D-Stratos\*"
WriteUninstaller "$INSTDIR\uninstall.exe"

!ifdef REG_START_MENU
!insertmacro MUI_STARTMENU_WRITE_BEGIN Application
CreateDirectory "$SMPROGRAMS\$SM_Folder"
CreateShortCut "$SMPROGRAMS\$SM_Folder\${APP_NAME}.lnk" "$INSTDIR\${MAIN_APP_EXE}"
CreateShortCut "$SMPROGRAMS\$SM_Folder\Uninstall ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe"

!ifdef WEB_SITE
WriteIniStr "$INSTDIR\BCN3D Stratos website.url" "InternetShortcut" "URL" "${WEB_SITE}"
CreateShortCut "$SMPROGRAMS\$SM_Folder\BCN3D Stratos website.lnk" "$INSTDIR\BCN3D Stratos website.url"
!endif
!insertmacro MUI_STARTMENU_WRITE_END
!endif

!ifndef REG_START_MENU
CreateDirectory "$SMPROGRAMS\BCN3D Stratos"
CreateShortCut "$SMPROGRAMS\BCN3D Stratos\${APP_NAME}.lnk" "$INSTDIR\${MAIN_APP_EXE}"
CreateShortCut "$SMPROGRAMS\BCN3D Stratos\Uninstall ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe"

!ifdef WEB_SITE
WriteIniStr "$INSTDIR\BCN3D Stratos website.url" "InternetShortcut" "URL" "${WEB_SITE}"
CreateShortCut "$SMPROGRAMS\BCN3D Stratos\BCN3D Stratos website.lnk" "$INSTDIR\BCN3D Stratos website.url"
!endif
!endif

WriteRegStr ${REG_ROOT} "${REG_APP_PATH}" ".\BCN3D-Stratos\BCN3D-Stratos.exe" "$INSTDIR\${MAIN_APP_EXE}"
WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}"  "DisplayName" "${APP_NAME}"
WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}"  "UninstallString" "$INSTDIR\uninstall.exe"
WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}"  "DisplayIcon" "$INSTDIR\${MAIN_APP_EXE}"
WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}"  "DisplayVersion" "${VERSION}"
WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}"  "Publisher" "${COMP_NAME}"

!ifdef WEB_SITE
WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}"  "URLInfoAbout" "${WEB_SITE}"
!endif
SectionEnd

######################################################################

Section UrlProtocol
SectionIn RO

; Register the URL schemes for the user that launches Stratos. Writing to
; HKCU explicitly also repairs an older, empty per-user protocol command that
; would otherwise override a valid machine-wide HKCR registration.
WriteRegStr HKCU "Software\Classes\cura" "" "URL:BCN3D Stratos Protocol"
WriteRegStr HKCU "Software\Classes\cura" "URL Protocol" ""
WriteRegStr HKCU "Software\Classes\cura\DefaultIcon" "" "$INSTDIR\${MAIN_APP_EXE},1"
WriteRegStr HKCU "Software\Classes\cura\shell" "" "open"
WriteRegStr HKCU "Software\Classes\cura\shell\open\command" "" '"$INSTDIR\${MAIN_APP_EXE}" --single-instance "%1"'

WriteRegStr HKCU "Software\Classes\slicer" "" "URL:BCN3D Stratos Protocol"
WriteRegStr HKCU "Software\Classes\slicer" "URL Protocol" ""
WriteRegStr HKCU "Software\Classes\slicer\DefaultIcon" "" "$INSTDIR\${MAIN_APP_EXE},1"
WriteRegStr HKCU "Software\Classes\slicer\shell" "" "open"
WriteRegStr HKCU "Software\Classes\slicer\shell\open\command" "" '"$INSTDIR\${MAIN_APP_EXE}" --single-instance "%1"'

SectionEnd

######################################################################

Section Uninstall
${INSTALL_TYPE}

# FIXME: dirty solution, but for some reason these directories aren't removed
RmDir "$INSTDIR\share\cura\resources\scripts"
RmDir "$INSTDIR\share\cura\resources"
RmDir "$INSTDIR\share\cura"
RmDir "$INSTDIR\share\uranium\resources\scripts"
RmDir "$INSTDIR\share\uranium\resources"
RmDir "$INSTDIR\share\uranium"
RmDir "$INSTDIR\share"

Delete "$INSTDIR\uninstall.exe"
!ifdef WEB_SITE
Delete "$INSTDIR\${APP_NAME} website.url"
!endif

RmDir /r /REBOOTOK "$INSTDIR"

!ifdef REG_START_MENU
!insertmacro MUI_STARTMENU_GETFOLDER "Application" $SM_Folder
Delete "$SMPROGRAMS\$SM_Folder\${APP_NAME}.lnk"
Delete "$SMPROGRAMS\$SM_Folder\Uninstall ${APP_NAME}.lnk"
!ifdef WEB_SITE
Delete "$SMPROGRAMS\$SM_Folder\BCN3D Stratos website.lnk"
!endif
RmDir "$SMPROGRAMS\$SM_Folder"
!endif

!ifndef REG_START_MENU
Delete "$SMPROGRAMS\BCN3D Stratos\${APP_NAME}.lnk"
Delete "$SMPROGRAMS\BCN3D Stratos\Uninstall ${APP_NAME}.lnk"
!ifdef WEB_SITE
Delete "$SMPROGRAMS\BCN3D Stratos\BCN3D Stratos website.lnk"
!endif
RmDir "$SMPROGRAMS\BCN3D Stratos"
!endif

!insertmacro APP_UNASSOCIATE "stl" "Cura.model"
!insertmacro APP_UNASSOCIATE "3mf" "Cura.project"

DeleteRegKey HKCU "Software\Classes\cura"
DeleteRegKey HKCU "Software\Classes\slicer"

DeleteRegKey ${REG_ROOT} "${REG_APP_PATH}"
DeleteRegKey ${REG_ROOT} "${UNINSTALL_PATH}"
SectionEnd

######################################################################

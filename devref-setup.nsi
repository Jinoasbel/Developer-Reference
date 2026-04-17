; ============================================================================
;  devref — NSIS Installer Script  (v2.0 — fixed)
;  Personal Developer Reference CLI
; ============================================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"

; ── General Settings ────────────────────────────────────────────────────────

Name "devref"
OutFile "devref-setup.exe"
InstallDir "$PROGRAMFILES\devref"
InstallDirRegKey HKLM "Software\devref" "InstallDir"
RequestExecutionLevel admin

; FIX-NSIS-1: Unicode true enables proper UTF-8 rendering in all NSIS pages.
; Required to properly display the '—' in Add/Remove programs.
; IMPORTANT: Save this .nsi file as "UTF-8 with BOM" in your text editor!
Unicode True

; ── Version Info ────────────────────────────────────────────────────────────

VIProductVersion "2.0.0.0"
VIAddVersionKey "ProductName"    "devref"
VIAddVersionKey "ProductVersion" "2.0.0"
VIAddVersionKey "CompanyName"    "devref"
VIAddVersionKey "FileDescription" "Developer Reference CLI"
VIAddVersionKey "LegalCopyright" "MIT"

; ── MUI Interface Settings ──────────────────────────────────────────────────

!define MUI_ABORTWARNING
!define MUI_ICON    "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON  "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; ── Installer Pages ─────────────────────────────────────────────────────────

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "devref_guide.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ── Uninstaller Pages ───────────────────────────────────────────────────────

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; ── Language ────────────────────────────────────────────────────────────────

!insertmacro MUI_LANGUAGE "English"

; ── Installer Section ───────────────────────────────────────────────────────

Section "Install" SecInstall

    SetOutPath "$INSTDIR"

    ; ── Copy application files ──────────────────────────────────────────────
    File "devref.exe"
    File "devref.py"
    File "devref.bat"
    File "devref_guide.txt"

    ; ── Create data subdirectory and copy JSON files ────────────────────────
    CreateDirectory "$INSTDIR\ref"

    ; FIX-NSIS-2: v2.0 renamed ref.json -> tools.json and syntax.json -> snippets.json.
    ; Migrate old ref.json -> tools.json if upgrading from v1
    IfFileExists "$INSTDIR\ref\ref.json" 0 no_old_ref
        IfFileExists "$INSTDIR\ref\tools.json" no_old_ref 0
            Rename "$INSTDIR\ref\ref.json" "$INSTDIR\ref\tools.json"
    no_old_ref:

    ; Migrate old syntax.json -> snippets.json if upgrading from v1
    IfFileExists "$INSTDIR\ref\syntax.json" 0 no_old_syn
        IfFileExists "$INSTDIR\ref\snippets.json" no_old_syn 0
            Rename "$INSTDIR\ref\syntax.json" "$INSTDIR\ref\snippets.json"
    no_old_syn:

    ; Only copy sample JSON files if they don't already exist (preserve user data)
    IfFileExists "$INSTDIR\ref\tools.json" +2 0
        File "/oname=ref\tools.json" "tools.json"

    IfFileExists "$INSTDIR\ref\snippets.json" +2 0
        File "/oname=ref\snippets.json" "snippets.json"

    ; ── Add to System PATH ──────────────────────────────────────────────────
    ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"

    StrLen $1 "$INSTDIR"
    StrLen $2 $0
    ${If} $2 > 0
        Push $0
        Push "$INSTDIR"
        Call StrContains
        Pop $3
        StrCmp $3 "" 0 path_already_set
    ${EndIf}

    StrCmp $0 "" 0 +3
        WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" "$INSTDIR"
        Goto path_done
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" "$0;$INSTDIR"

    path_already_set:
    path_done:

    ; Broadcast environment change so open terminals pick it up
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

    ; ── Write Uninstaller ───────────────────────────────────────────────────
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; ── Write Registry Keys for Add/Remove Programs ─────────────────────────
    WriteRegStr HKLM "Software\devref" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "DisplayName" "devref — Developer Reference CLI"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "DisplayVersion" "2.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "Publisher" "devref"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "NoRepair" 1

    ; ── Estimate installed size ─────────────────────────────────────────────
    SectionGetSize ${SecInstall} $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "EstimatedSize" $0

SectionEnd

; ── String Contains Function ────────────────────────────────────────────────

Function StrContains
    Exch $1 ; needle
    Exch
    Exch $2 ; haystack
    Push $3
    Push $4
    Push $5
    StrLen $3 $1
    StrLen $4 $2
    ${If} $3 > $4
        StrCpy $1 ""
        Goto done
    ${EndIf}
    IntOp $4 $4 - $3
    StrCpy $5 0
    loop:
        IntCmp $5 $4 0 0 notfound
        StrCpy $0 $2 $3 $5
        StrCmp $0 $1 found
        IntOp $5 $5 + 1
        Goto loop
    found:
        Goto done
    notfound:
        StrCpy $1 ""
    done:
        Pop $5
        Pop $4
        Pop $3
        Pop $2
        Exch $1
FunctionEnd

; ── Uninstaller Section ─────────────────────────────────────────────────────

Section "Uninstall"

    ; ── Remove from System PATH ─────────────────────────────────────────────
    ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"

    Push $0
    Push "$INSTDIR"
    Call un.RemoveFromPath
    Pop $0
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" $0

    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

    ; ── Remove application files ────────────────────────────────────────────
    Delete "$INSTDIR\devref.exe"
    Delete "$INSTDIR\devref.py"
    Delete "$INSTDIR\devref.bat"
    Delete "$INSTDIR\devref_guide.txt"
    Delete "$INSTDIR\uninstall.exe"

    ; ── Remove data files ───────────────────────────────────────────────────
    Delete "$INSTDIR\ref\tools.json"
    Delete "$INSTDIR\ref\snippets.json"
    Delete "$INSTDIR\ref\meta.json"
    
    ; Clean up any leftover v1 files from upgrade
    Delete "$INSTDIR\ref\ref.json"
    Delete "$INSTDIR\ref\syntax.json"
    RMDir  "$INSTDIR\ref"

    ; ── Remove backups directory (if exists) ────────────────────────────────
    RMDir /r "$INSTDIR\backups"

    ; ── Remove install directory ────────────────────────────────────────────
    RMDir "$INSTDIR"

    ; ── Clean up Registry ───────────────────────────────────────────────────
    DeleteRegKey HKLM "Software\devref"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref"

SectionEnd

; ── Remove From Path Function (Uninstaller) ─────────────────────────────────

Function un.RemoveFromPath
    Exch $1 ; dir to remove
    Exch
    Exch $2 ; full path
    Push $3
    Push $4
    Push $5
    Push $6

    StrCpy $3 ""
    StrCpy $4 $2

    loop:
        StrLen $6 $4
        ${If} $6 == 0
            Goto done
        ${EndIf}

        Push $4
        Push ";"
        Call un.StrStr
        Pop $5

        ${If} $5 == ""
            StrCmp $4 $1 skip_last
            StrCmp $3 "" 0 +3
                StrCpy $3 $4
                Goto done
            StrCpy $3 "$3;$4"
            Goto done
            skip_last:
            Goto done
        ${EndIf}

        StrLen $6 $5
        StrLen $0 $4
        IntOp $0 $0 - $6
        StrCpy $6 $4 $0

        StrCmp $6 $1 skip_segment
        StrCmp $3 "" 0 +3
            StrCpy $3 $6
            Goto advance
        StrCpy $3 "$3;$6"
        Goto advance

        skip_segment:
        advance:
        StrLen $0 $4
        StrLen $6 $5
        IntOp $6 $6 - 1
        ${If} $6 > 0
            StrCpy $4 $5 "" 1
        ${Else}
            StrCpy $4 ""
        ${EndIf}
        Goto loop

    done:
    Pop $6
    Pop $5
    Pop $4
    Pop $2
    Exch $1
    StrCpy $1 $3
    Exch $1
FunctionEnd

; ── StrStr for Uninstaller ──────────────────────────────────────────────────

Function un.StrStr
    Exch $1 ; needle
    Exch
    Exch $2 ; haystack
    Push $3
    Push $4
    Push $5
    StrLen $3 $1
    StrLen $4 $2
    ${If} $3 > $4
        StrCpy $1 ""
        Goto done
    ${EndIf}
    IntOp $4 $4 - $3
    StrCpy $5 0
    loop:
        IntCmp $5 $4 0 0 notfound
        StrCpy $0 $2 $3 $5
        StrCmp $0 $1 found
        IntOp $5 $5 + 1
        Goto loop
    found:
        StrCpy $1 $2 "" $5
        Goto done
    notfound:
        StrCpy $1 ""
    done:
        Pop $5
        Pop $4
        Pop $3
        Pop $2
        Exch $1
FunctionEnd
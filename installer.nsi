; ============================================================================
;  devref — NSIS Installer Script
;  Personal Developer Reference CLI
; ============================================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"

; ── General Settings ──────────────────────────────────────────────────────────

Name "devref"
OutFile "devref-setup.exe"
InstallDir "$PROGRAMFILES\devref"
InstallDirRegKey HKLM "Software\devref" "InstallDir"
RequestExecutionLevel admin
Unicode True

; ── Version Info ──────────────────────────────────────────────────────────────

VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "devref"
VIAddVersionKey "ProductVersion" "1.0.0"
VIAddVersionKey "CompanyName" "devref"
VIAddVersionKey "FileDescription" "devref — Personal Developer Reference CLI"
VIAddVersionKey "LegalCopyright" "MIT"

; ── MUI Interface Settings ────────────────────────────────────────────────────

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; ── Installer Pages ───────────────────────────────────────────────────────────

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "devref_guide.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ── Uninstaller Pages ─────────────────────────────────────────────────────────

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; ── Language ──────────────────────────────────────────────────────────────────

!insertmacro MUI_LANGUAGE "English"

; ── Installer Section ─────────────────────────────────────────────────────────

Section "Install" SecInstall

    SetOutPath "$INSTDIR"

    ; ── Copy application files ────────────────────────────────────────────────
    File "devref.exe"
    File "devref.py"
    File "devref.bat"
    File "devref_guide.txt"

    ; ── Create data subdirectory and copy JSON files ──────────────────────────
    CreateDirectory "$INSTDIR\ref"

    ; Only copy sample JSON files if they don't already exist (preserve user data)
    IfFileExists "$INSTDIR\ref\ref.json" +2 0
        File "/oname=ref\ref.json" "ref.json"

    IfFileExists "$INSTDIR\ref\syntax.json" +2 0
        File "/oname=ref\syntax.json" "syntax.json"

    ; ── Add to System PATH ────────────────────────────────────────────────────
    ; Read current system PATH
    ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"

    ; Check if our path is already in there (avoid duplicates)
    StrLen $1 "$INSTDIR"
    StrLen $2 $0
    ${If} $2 > 0
        ; Search for INSTDIR in current PATH
        Push $0
        Push "$INSTDIR"
        Call StrContains
        Pop $3
        StrCmp $3 "" 0 path_already_set
    ${EndIf}

    ; Append our install dir to PATH
    StrCmp $0 "" 0 +3
        WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" "$INSTDIR"
        Goto path_done
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" "$0;$INSTDIR"

    path_already_set:
    path_done:

    ; Broadcast environment change so open terminals pick it up
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

    ; ── Write Uninstaller ─────────────────────────────────────────────────────
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; ── Write Registry Keys for Add/Remove Programs ──────────────────────────
    WriteRegStr HKLM "Software\devref" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "DisplayName" "devref — Developer Reference CLI"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "Publisher" "devref"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "NoRepair" 1

    ; ── Estimate installed size ───────────────────────────────────────────────
    SectionGetSize ${SecInstall} $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "EstimatedSize" $0

SectionEnd

; ── String Contains Function ──────────────────────────────────────────────────
; Usage: Push "haystack" / Push "needle" / Call StrContains / Pop $result
; Returns needle if found, empty string if not found

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

; ── Uninstaller Section ───────────────────────────────────────────────────────

Section "Uninstall"

    ; ── Remove from System PATH ───────────────────────────────────────────────
    ReadRegStr $0 HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path"

    ; Remove $INSTDIR from PATH string
    Push $0
    Push "$INSTDIR"
    Call un.RemoveFromPath
    Pop $0
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "Path" $0

    ; Broadcast environment change
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000

    ; ── Remove application files ──────────────────────────────────────────────
    Delete "$INSTDIR\devref.exe"
    Delete "$INSTDIR\devref.py"
    Delete "$INSTDIR\devref.bat"
    Delete "$INSTDIR\devref_guide.txt"
    Delete "$INSTDIR\uninstall.exe"

    ; ── Remove data files ─────────────────────────────────────────────────────
    Delete "$INSTDIR\ref\ref.json"
    Delete "$INSTDIR\ref\syntax.json"
    Delete "$INSTDIR\ref\meta.json"
    RMDir "$INSTDIR\ref"

    ; ── Remove backups directory (if exists) ──────────────────────────────────
    RMDir /r "$INSTDIR\backups"

    ; ── Remove install directory ──────────────────────────────────────────────
    RMDir "$INSTDIR"

    ; ── Clean up Registry ─────────────────────────────────────────────────────
    DeleteRegKey HKLM "Software\devref"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref"

SectionEnd

; ── Remove From Path Function (Uninstaller) ───────────────────────────────────
; Removes a directory from a semicolon-delimited PATH string
; Usage: Push "full path string" / Push "dir to remove" / Call un.RemoveFromPath / Pop $result

Function un.RemoveFromPath
    Exch $1 ; dir to remove
    Exch
    Exch $2 ; full path
    Push $3
    Push $4
    Push $5
    Push $6

    StrCpy $3 ""  ; result
    StrCpy $4 $2  ; remaining

    loop:
        ; Find next semicolon
        StrLen $6 $4
        ${If} $6 == 0
            Goto done
        ${EndIf}

        Push $4
        Push ";"
        Call un.StrStr
        Pop $5

        ${If} $5 == ""
            ; No more semicolons — last segment
            StrCmp $4 $1 skip_last
            StrCmp $3 "" 0 +3
                StrCpy $3 $4
                Goto done
            StrCpy $3 "$3;$4"
            Goto done
            skip_last:
            Goto done
        ${EndIf}

        ; Extract segment before semicolon
        StrLen $6 $5
        StrLen $0 $4
        IntOp $0 $0 - $6
        StrCpy $6 $4 $0

        ; Skip if this segment matches the dir to remove
        StrCmp $6 $1 skip_segment
        StrCmp $3 "" 0 +3
            StrCpy $3 $6
            Goto advance
        StrCpy $3 "$3;$6"
        Goto advance

        skip_segment:
        advance:
        ; Move past the semicolon
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

; ── StrStr for Uninstaller ────────────────────────────────────────────────────
; Find first occurrence of needle in haystack
; Push haystack / Push needle / Call un.StrStr / Pop result

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

;==========================================
; NSIS Script: devref_setup.nsi
; Purpose: Installer for devref (PyInstaller --onedir build) — MIT license,
;          user agreement, PATH integration, completion page.
;
; EXPECTED SOURCE LAYOUT (PyInstaller --onedir output):
; -------------------------------------------------------
;   devref\
;     devref.exe          ← main launcher
;     _internal\          ← Python runtime, .pyd, .dll, data files
;       python3xx.dll
;       ...
;
; Build the installer from the directory that CONTAINS the devref\ folder,
; e.g.:  makensis devref_setup.nsi
; (devref_setup.nsi sits next to the devref\ folder, not inside it.)
; Author:  Asbel Jino K  /  2026
;
; BUGS FIXED vs the original draft
; ----------------------------------
; [1] VIProductVersion "2.1" → "2.1.0.0"  (NSIS requires 4-part numeric)
; [2] IsPathInEnv — original loop never advanced its index past offset 0,
;     causing an infinite loop on any non-empty PATH.  Replaced with a
;     sentinel-semicolon + StrStr approach.
; [3] StrStr helper added (required by the new IsPathInEnv).
; [4] un.RemoveFromPath — three original bugs:
;       a. Used bare $5 (not a valid NSIS register) → replaced with $R5.
;       b. "Goto loop" inside un-function jumped to the wrong label
;          (installer function's label) → corrected to "Goto unloop".
;       c. "undone:" label was placed after the cleanup code, so the
;          last PATH segment was never flushed into the result.
;          Label position corrected; stack unwind verified push-for-pop.
; [5] Argument push order for IsPathInEnv and un.RemoveFromPath corrected
;     (PATH string must be pushed first / deeper; path-to-act-on on top).
; [6] Stray escaped quotes "$\"box below$\"" removed from agreement text.
; [7] NSD_CreateLabel return handles now Pop'd in both custom pages.
;==========================================

;-------------------------------------------
; Installer Configuration
;-------------------------------------------

Name            "devref"
OutFile         "devref_setup.exe"
InstallDir      "$PROGRAMFILES\devref"
InstallDirRegKey HKLM "Software\devref" "Install_Dir"
RequestExecutionLevel admin

; FIX [1]: four-part numeric version required by NSIS
VIProductVersion "2.1.0.0"
VIAddVersionKey "ProductName"     "devref"
VIAddVersionKey "DeveloperName"   "Asbel Jino K"
VIAddVersionKey "LegalCopyright"  "MIT License"
VIAddVersionKey "FileDescription" "devref Setup"
VIAddVersionKey "FileVersion"     "2.1.0.0"

SetCompressor /SOLID lzma
SetCompressorDictSize 32

;-------------------------------------------
; MUI
;-------------------------------------------

!include "MUI.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "WinMessages.nsh"
!include "nsDialogs.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON   "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;-------------------------------------------
; Pages
;-------------------------------------------

!insertmacro MUI_PAGE_WELCOME

!define MUI_LICENSEPAGE_TEXT_TOP "Please review the MIT License terms before installing devref."
!define MUI_LICENSEPAGE_BUTTON   "I &Agree"
!define MUI_LICENSEPAGE_CHECKBOX
!insertmacro MUI_PAGE_LICENSE "mit_license.txt"

Page custom UserAgreementPage UserAgreementLeave

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

Page custom CompletionPage

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

;-------------------------------------------
; Variables
;-------------------------------------------

Var UserAgreementCheckbox

;===================================================================
; USER AGREEMENT PAGE
;===================================================================

Function UserAgreementPage
    !insertmacro MUI_HEADER_TEXT "User Agreement" "Please read and accept the following terms"

    nsDialogs::Create 1018
    Pop $0
    ${If} $0 == error
        Abort
    ${EndIf}

    ; FIX [6]: no escaped quotes around "box below"
    ; FIX [7]: Pop the handle returned by NSD_CreateLabel
    ${NSD_CreateLabel} 0 0 100% 120u \
        "devref User Agreement$\n$\n\
===================================$\n$\n\
1. NO DATA COLLECTION$\n\
   We do NOT collect, store, or transmit any personal information.$\n\
   This application operates entirely offline.$\n$\n\
2. INDIE DEVELOPED$\n\
   This project is developed by independent developers.$\n\
   It is provided as-is with no guarantees or warranties.$\n$\n\
3. LIABILITY DISCLAIMER$\n\
   The developers are not responsible for any bugs, errors,$\n\
   data loss, system damage, or other issues from using this$\n\
   software.  Use at your own risk.$\n$\n\
4. OPEN SOURCE$\n\
   Released under the MIT License.  You may view, modify,$\n\
   and distribute the source code freely.$\n$\n\
5. SUPPORT$\n\
   Support is best-effort, community-based.  No guarantees.$\n$\n\
===================================$\n$\n\
By checking the box below you acknowledge and agree to these terms."
    Pop $0   ; discard label handle

    ${NSD_CreateCheckbox} 0 130u 100% 10u "&I have read and agree to the above terms"
    Pop $UserAgreementCheckbox
    ${NSD_OnClick} $UserAgreementCheckbox UserAgreementCheckboxClick

    ; Disable Next until the checkbox is ticked
    GetDlgItem $0 $HWNDPARENT 1
    EnableWindow $0 0

    nsDialogs::Show
FunctionEnd

Function UserAgreementCheckboxClick
    ${NSD_GetState} $UserAgreementCheckbox $0
    GetDlgItem $1 $HWNDPARENT 1
    ${If} $0 == ${BST_CHECKED}
        EnableWindow $1 1
    ${Else}
        EnableWindow $1 0
    ${EndIf}
FunctionEnd

Function UserAgreementLeave
    ${NSD_GetState} $UserAgreementCheckbox $0
    ${If} $0 != ${BST_CHECKED}
        MessageBox MB_ICONEXCLAMATION "You must accept the user agreement to continue."
        Abort
    ${EndIf}
FunctionEnd

;===================================================================
; COMPLETION PAGE
;===================================================================

Function CompletionPage
    !insertmacro MUI_HEADER_TEXT "Welcome to devref!" "Installation complete"

    nsDialogs::Create 1018
    Pop $0
    ${If} $0 == error
        Abort
    ${EndIf}

    ; FIX [7]: Pop the handle
    ${NSD_CreateLabel} 0 0 100% 100% \
        "==========================================$\n$\n\
WELCOME TO DEVREF!$\n$\n\
==========================================$\n$\n\
Thank you for installing devref!$\n$\n\
Installation Information:$\n\
  - Installed to: $INSTDIR$\n\
  - $INSTDIR has been added to your system PATH.$\n\
    You can now run 'devref' from any terminal.$\n$\n\
IMPORTANT NOTES:$\n\
  - Provided 'as-is' without any warranties.$\n\
  - Developers are not liable for any issues or data loss.$\n\
  - No personal information is collected.$\n\
  - MIT-licensed, open-source, indie project.$\n\
  - Report bugs on our GitHub repository.$\n\
  - Keep the software updated for security fixes.$\n$\n\
==========================================$\n$\n\
Press Finish to complete setup."
    Pop $0   ; discard label handle

    nsDialogs::Show
FunctionEnd

;===================================================================
; INSTALL SECTION
;===================================================================

Section "Install devref" SecInstall

    SetOutPath $INSTDIR

    ; ------------------------------------------------------------------
    ; Copy the entire PyInstaller --onedir output tree.
    ; "devref" is the folder produced by PyInstaller sitting next to this
    ; script.  File /r copies devref.exe + _internal\ (DLLs, .pyd, data)
    ; preserving the sub-directory structure under $INSTDIR.
    ; ------------------------------------------------------------------
    File /r "devref\*.*"

    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; ------------------------------------------------------------------
    ; Add $INSTDIR to the system PATH (skip if already present)
    ; FIX [5]: PATH string pushed first (deeper), search target on top.
    ; ------------------------------------------------------------------
    ReadRegStr $0 HKLM \
        "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "PATH"

    ${If} $0 != ""
        Push "$0"       ; PATH string  — pushed first, sits deeper
        Push "$INSTDIR" ; path to find — pushed last, on top
        Call IsPathInEnv
        Pop $1          ; 1 = already in PATH, 0 = not present

        ${If} $1 == 0
            StrCpy $0 "$0;$INSTDIR"
            WriteRegExpandStr HKLM \
                "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" \
                "PATH" "$0"
            SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 \
                "STR:Environment" /TIMEOUT=5000
        ${EndIf}
    ${Else}
        WriteRegExpandStr HKLM \
            "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" \
            "PATH" "$INSTDIR"
        SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 \
            "STR:Environment" /TIMEOUT=5000
    ${EndIf}

    ; ------------------------------------------------------------------
    ; Register with Windows Add/Remove Programs
    ; ------------------------------------------------------------------
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "DisplayName" "devref"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "DisplayIcon" "$INSTDIR\devref.exe"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "Publisher" "Indie Developer"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "HelpLink" "https://github.com/yourusername/devref/issues"
    WriteRegDWORD HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "NoModify" 1
    WriteRegDWORD HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref" \
        "NoRepair" 1

    ; Optional Start Menu shortcuts — uncomment to enable:
    ; CreateDirectory "$SMPROGRAMS\devref"
    ; CreateShortCut "$SMPROGRAMS\devref\devref.lnk"    "$INSTDIR\devref.exe"
    ; CreateShortCut "$SMPROGRAMS\devref\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

SectionEnd

;===================================================================
; HELPER: StrStr
; Case-sensitive substring search.
;
; Stack in:  [top] needle   [next] haystack
; Stack out: [top] tail of haystack from first match, or "" if absent
;===================================================================

Function StrStr
    Exch $R1        ; $R1 = needle
    Exch
    Exch $R0        ; $R0 = haystack
    Push $R2        ; needle length
    Push $R3        ; character window / single char
    Push $R4        ; walking index

    StrLen $R2 $R1
    StrCpy $R4 0

  ss_loop:
    StrCpy $R3 $R0 $R2 $R4     ; window of needle-length at position $R4
    ${If} $R3 == $R1
        StrCpy $R0 $R0 "" $R4  ; slice from match position to end
        Goto ss_done
    ${EndIf}
    StrCpy $R3 $R0 1 $R4       ; single char — detect end-of-string
    ${If} $R3 == ""
        StrCpy $R0 ""
        Goto ss_done
    ${EndIf}
    IntOp $R4 $R4 + 1
    Goto ss_loop

  ss_done:
    Pop $R4
    Pop $R3
    Pop $R2
    Pop $R1
    Exch $R0
FunctionEnd

;===================================================================
; HELPER: IsPathInEnv
; Checks whether a directory already exists in a PATH string.
; Wraps both in semicolons to prevent false positives on substrings.
;
; Stack in:  [top] path-to-find   [next] PATH string
; Stack out: [top] 1 if found, 0 if not found
;
; FIX [2]: original loop had a fixed offset of 0 on every iteration.
;===================================================================

Function IsPathInEnv
    Exch $R0        ; $R0 = path to find
    Exch
    Exch $R1        ; $R1 = full PATH string
    Push $R2

    ; e.g. PATH = "C:\foo;C:\bar"  →  wrapped = ";C:\foo;C:\bar;"
    ;      entry = "C:\foo"         →  needle  = ";C:\foo;"
    StrCpy $R2 ";$R1;"
    Push $R2
    Push ";$R0;"
    Call StrStr
    Pop $R2

    ${If} $R2 == ""
        StrCpy $R0 0
    ${Else}
        StrCpy $R0 1
    ${EndIf}

    Pop $R2
    Pop $R1
    Exch $R0
FunctionEnd

;===================================================================
; UNINSTALL SECTION
;===================================================================

Section "Uninstall"

    ; ------------------------------------------------------------------
    ; Remove everything installed — the full onedir tree including
    ; _internal\ and the uninstaller itself.
    ; RMDir /r handles non-empty directories safely.
    ; ------------------------------------------------------------------
    RMDir /r "$INSTDIR"

    ; ------------------------------------------------------------------
    ; Remove $INSTDIR from system PATH
    ; FIX [5]: same push-order fix as installer section
    ; ------------------------------------------------------------------
    ReadRegStr $0 HKLM \
        "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "PATH"

    ${If} $0 != ""
        Push "$0"       ; PATH string  — pushed first, sits deeper
        Push "$INSTDIR" ; path to remove — pushed last, on top
        Call un.RemoveFromPath
        Pop $1          ; cleaned PATH string

        WriteRegExpandStr HKLM \
            "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" \
            "PATH" "$1"
        SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 \
            "STR:Environment" /TIMEOUT=5000
    ${EndIf}

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\devref"
    DeleteRegKey HKLM "Software\devref"

    ; Optional Start Menu cleanup:
    ; Delete "$SMPROGRAMS\devref\devref.lnk"
    ; Delete "$SMPROGRAMS\devref\Uninstall.lnk"
    ; RMDir  "$SMPROGRAMS\devref"

SectionEnd

;===================================================================
; HELPER: un.RemoveFromPath
; Removes one semicolon-delimited entry from a PATH string.
;
; Stack in:  [top] path-to-remove   [next] PATH string
; Stack out: [top] cleaned PATH string
;
; FIX [4a]: bare $5 → $R5
; FIX [4b]: "Goto loop" → "Goto unloop"
; FIX [4c]: "undone:" moved before result-flush so last segment is kept;
;           stack unwind verified push-for-pop.
;
; Push order on entry (deepest → top after both Exch):
;   old-$R1  old-$R0  $R2  $R3  $R4  $R5
; Pop order at undone: $R5 $R4 $R3 $R2 then $R1 via Pop, $R0 via Exch.
;===================================================================

Function un.RemoveFromPath
    ; Caller's stack: [top] path-to-remove   [next] PATH-string
    Exch $R0        ; $R0 ← path-to-remove;  stack: [old-$R0] [PATH-string]
    Exch            ;                         stack: [PATH-string] [old-$R0]
    Exch $R1        ; $R1 ← PATH-string;      stack: [old-$R1] [old-$R0]

    Push $R2        ; segment accumulator
    Push $R3        ; single character
    Push $R4        ; walking index
    Push $R5        ; result accumulator

    StrCpy $R2 ""
    StrCpy $R5 ""
    StrCpy $R4 0

  unloop:
    StrCpy $R3 $R1 1 $R4   ; read one char at position $R4
    IntOp $R4 $R4 + 1

    ${If} $R3 == ";"
        ; Flush current segment (unless it is the path we are removing)
        ${If} $R2 != ""
        ${AndIf} $R2 != $R0
            ${If} $R5 == ""
                StrCpy $R5 $R2
            ${Else}
                StrCpy $R5 "$R5;$R2"
            ${EndIf}
        ${EndIf}
        StrCpy $R2 ""   ; reset segment buffer
        Goto unloop
    ${EndIf}

    ${If} $R3 == ""
        ; End of string — flush the final segment
        ${If} $R2 != ""
        ${AndIf} $R2 != $R0
            ${If} $R5 == ""
                StrCpy $R5 $R2
            ${Else}
                StrCpy $R5 "$R5;$R2"
            ${EndIf}
        ${EndIf}
        Goto undone
    ${EndIf}

    ; Normal character — append to segment buffer
    StrCpy $R2 "$R2$R3"

    ${If} $R4 > 8192
        Goto undone     ; safety guard
    ${EndIf}
    Goto unloop

  undone:
    ; Move result into $R0 for return (overwrites path-to-remove, no longer needed)
    StrCpy $R0 $R5

    ; Restore saved registers in reverse push order
    Pop $R5
    Pop $R4
    Pop $R3
    Pop $R2
    Pop $R1     ; restores old $R1; stack: [old-$R0]

    ; Replace old-$R0 on stack with our result ($R0 = cleaned PATH)
    Exch $R0    ; stack top = cleaned PATH string  ← returned to caller
FunctionEnd

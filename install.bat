@echo off
setlocal enabledelayedexpansion

echo.
echo  =============================================
echo   devref Installer
echo  =============================================
echo.

REM ── Check S: drive exists
if not exist "S:\" (
    echo  [ERROR] S: drive not found. Please connect your S: drive and retry.
    pause
    exit /b 1
)

REM ── Create directories
echo  [1/4] Creating folders on S:\devref\ref\ ...
mkdir "S:\devref\ref" 2>nul
echo        Done.

REM ── Copy exe
echo  [2/4] Copying devref.exe to S:\devref\ ...
copy /Y "devref.exe" "S:\devref\devref.exe" >nul
if errorlevel 1 (
    echo  [ERROR] Could not copy devref.exe. Make sure it is in the same folder as this installer.
    pause
    exit /b 1
)
echo        Done.

REM ── Copy JSON files if they don't already exist
echo  [3/4] Setting up data files ...
if not exist "S:\devref\ref\ref.json" (
    copy /Y "ref.json" "S:\devref\ref\ref.json" >nul
    echo        ref.json created with sample data.
) else (
    echo        ref.json already exists, skipping.
)

if not exist "S:\devref\ref\syntax.json" (
    copy /Y "syntax.json" "S:\devref\ref\syntax.json" >nul
    echo        syntax.json created with sample data.
) else (
    echo        syntax.json already exists, skipping.
)

REM ── Copy guide
copy /Y "devref_guide.txt" "S:\devref\devref_guide.txt" >nul

echo  [4/4] Done!
echo.
echo  =============================================
echo   MANUAL STEP REQUIRED: Add to PATH
echo  =============================================
echo.
echo  To use  devref  from any terminal window:
echo.
echo  1. Press  Win + R  and type:  sysdm.cpl
echo  2. Go to  Advanced  tab
echo  3. Click  Environment Variables
echo  4. Under  System variables  find  Path  and click  Edit
echo  5. Click  New  and paste:
echo.
echo       S:\devref
echo.
echo  6. Click OK on all dialogs
echo  7. Open a NEW terminal and type:  devref --help
echo.
echo  =============================================
echo.
pause

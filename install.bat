@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo  =============================================
echo   devref Installer v2.0
echo  =============================================
echo.

REM Check S: drive exists
if not exist "S:\" (
    echo  [ERROR] S: drive not found. Connect your S: drive and retry.
    pause
    exit /b 1
)

REM Create directories
echo  [1/4] Creating folders on S:\devref\ref\ ...
mkdir "S:\devref\ref" 2>nul
echo        Done.

REM Copy exe
echo  [2/4] Copying devref.exe to S:\devref\ ...
copy /Y "devref.exe" "S:\devref\devref.exe" >nul
if errorlevel 1 (
    echo  [ERROR] Could not copy devref.exe.
    echo         Make sure devref.exe is in the same folder as this installer.
    pause
    exit /b 1
)
echo        Done.

REM Copy JSON data files
echo  [3/4] Setting up data files ...

if not exist "S:\devref\ref\tools.json" (
    copy /Y "tools.json" "S:\devref\ref\tools.json" >nul
    echo        tools.json created with sample data.
) else (
    echo        tools.json already exists, skipping.
)

if not exist "S:\devref\ref\snippets.json" (
    copy /Y "snippets.json" "S:\devref\ref\snippets.json" >nul
    echo        snippets.json created with sample data.
) else (
    echo        snippets.json already exists, skipping.
)

REM Copy guide
copy /Y "devref_guide.txt" "S:\devref\devref_guide.txt" >nul 2>nul

echo  [4/4] Done!
echo.
echo  =============================================
echo   MANUAL STEP: Add devref to PATH
echo  =============================================
echo.
echo  So you can run devref from any terminal:
echo.
echo  1. Press Win + R  and type:  sysdm.cpl  then Enter
echo  2. Click the  Advanced  tab
echo  3. Click  Environment Variables
echo  4. Under  System variables  find  Path  and click  Edit
echo  5. Click  New  and type:
echo.
echo       S:\devref
echo.
echo  6. Click OK on all dialogs
echo  7. Open a NEW terminal window
echo  8. Type:  devref --help
echo.
echo  =============================================
echo.
pause

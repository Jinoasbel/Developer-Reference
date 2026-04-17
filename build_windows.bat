@echo off
chcp 65001 >nul
echo.
echo  ================================================
echo   devref v2.0 -- Build Script
echo   Run this on your Windows PC to create the exe
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo         Install from https://python.org and try again.
    pause
    exit /b 1
)

echo  [1/3] Installing dependencies...
pip install pyinstaller colorama rapidfuzz prompt_toolkit --quiet
if errorlevel 1 (
    echo  [ERROR] pip install failed.
    pause
    exit /b 1
)

echo  [2/3] Compiling devref.exe...
pyinstaller --onefile --name devref --distpath . devref.py
if errorlevel 1 (
    echo  [ERROR] Compilation failed. Check the output above.
    pause
    exit /b 1
)

echo  [3/3] Cleaning up build files...
rmdir /s /q build 2>nul
del devref.spec 2>nul

echo.
echo  ================================================
echo   devref.exe built successfully!
echo   Now run install.bat to set it up on S: drive
echo  ================================================
echo.
pause

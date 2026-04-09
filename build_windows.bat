@echo off
echo.
echo  ================================================
echo   devref — Build Script (run this on your PC)
echo  ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python from https://python.org
    pause
    exit /b 1
)

echo  [1/3] Installing dependencies...
pip install pyinstaller colorama rapidfuzz --quiet
if errorlevel 1 (
    echo  [ERROR] pip install failed.
    pause
    exit /b 1
)

echo  [2/3] Compiling devref.exe...
pyinstaller --onefile --name devref --distpath . devref.py
if errorlevel 1 (
    echo  [ERROR] Compilation failed.
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

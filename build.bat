@echo off
REM build.bat - Build script for Windows

echo Building Risk Manager...

REM Activate virtual environment if not already active
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

REM Install PyInstaller if not already installed
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with PyInstaller
echo Building executable...
pyinstaller --onefile --windowed --name "RiskManager" --add-data "src;src" --add-binary "C:\Program Files\Tesseract-OCR\tesseract.exe;." src/main.py

REM Alternative: Use spec file for more control
REM pyinstaller build.spec

echo Build complete!
echo Executable located in: dist\RiskManager.exe
pause
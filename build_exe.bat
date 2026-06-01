@echo off
echo Installing project...
pip install -e ".[dev]"

echo Building Windows executable...
pyinstaller --onefile --windowed --name TDMS_Sync_Checker tdms_sync_checker_gui.py

echo.
echo Executable created in:
echo dist\TDMS_Sync_Checker.exe
pause

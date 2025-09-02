@echo off
REM Osaka - Video Cropping Tool
REM Windows batch wrapper for the Python script

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Change to the script directory to handle relative imports
pushd "%SCRIPT_DIR%"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

REM Run the Python script with all passed arguments
python "main.py" %*

REM Return to the original directory
popd

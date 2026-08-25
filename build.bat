@echo off
cls

echo ================================================
echo  Smart File Organizer Pro - One-Click Build
echo ================================================
echo.

REM ---- Ensure we are in project root ----
cd /d %~dp0

REM ---- Activate virtual environment ----
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate
) else (
    echo Virtual environment not found!
    echo Please create venv before building.
    pause
    exit /b 1
)

REM ---- Version is read automatically from app\version.py ----
REM     (release.py imports APP_VERSION and sets it for Inno Setup)
REM     Do NOT hardcode it here - update app\version.py instead.

echo Starting build...
echo.

REM ---- Run automated release ----
python release.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo  BUILD FAILED!
    echo ================================================
    pause
    exit /b 1
)

echo.
echo ================================================
echo  BUILD COMPLETED SUCCESSFULLY!
echo ================================================
echo.
echo Output files are in the release\ folder.
echo   - SmartFileOrganizer_Setup_v^<version^>.exe
echo   - SmartFileOrganizer_Portable_v^<version^>.zip
echo.
echo (version number comes from app\version.py)
echo.

pause
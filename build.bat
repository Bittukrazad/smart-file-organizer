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
    echo ❌ Virtual environment not found!
    echo Please create venv before building.
    pause
    exit /b 1
)

REM ---- Set version (single source of truth) ----
set APP_VERSION=1.0.0

echo Building version %APP_VERSION%
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

echo Output files:
echo   release\SmartFileOrganizer_Setup_v%APP_VERSION%.exe
echo   release\SmartFileOrganizer_Portable_v%APP_VERSION%.zip
echo.

pause

@echo off
title Advertpreneur - Amazon.de Scraper
color F0

echo.
echo  ================================================
echo   Advertpreneur - Amazon.de Scraper
echo  ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Download it from: https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b
)

:: Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  [SETUP] Installing Flask...
    pip install flask
)

:: Check if Playwright is installed
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo  [SETUP] Installing Playwright...
    pip install playwright
    echo  [SETUP] Installing Chromium browser...
    playwright install chromium
)

:: Check if Chromium is installed for Playwright
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.stop()" >nul 2>&1
if errorlevel 1 (
    echo  [SETUP] Installing Chromium browser...
    playwright install chromium
)

echo.
echo  [OK] All dependencies ready.
echo.
echo  Starting scraper server...
echo  Opening browser in 3 seconds...
echo.

:: Start the browser after a short delay
start /b cmd /c "timeout /t 3 >nul && start http://localhost:5000"

:: Run the Flask app
python app.py

echo.
echo  Server stopped.
pause

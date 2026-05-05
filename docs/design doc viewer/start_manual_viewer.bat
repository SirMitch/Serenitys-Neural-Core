@echo off
title AlphaChart v3.4 — Manual Viewer
color 0A

echo.
echo  ============================================
echo   AlphaChart v3.4 -- Design Manual Viewer
echo  ============================================
echo.
echo  Starting Streamlit viewer...
echo  Browser will open automatically.
echo  Press Ctrl+C in this window to stop.
echo.

cd /d "%~dp0"

:: Check if Streamlit is installed
where streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Streamlit not found. Installing...
    pip install streamlit
    echo.
)

:: Check if port 8501 is in use
echo Checking port 8501...
netstat -ano | find ":8501" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Port 8501 is already in use.
    echo Attempting to free the port...
    
    :: Find and kill the process using port 8501
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":8501"') do (
        echo Killing process with PID %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
    
    timeout /t 2 /nobreak >nul
    echo Port should now be free.
    echo.
)

:: Run Streamlit with explicit port and better options
echo Starting AlphaChart Manual Viewer...
streamlit run alphachart_manual_viewer.py ^
    --server.port 8501 ^
    --server.headless false ^
    --browser.gatherUsageStats false ^
    --server.runOnSave true

pause
@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title MANTIS STUDIO - NEON TECH-NOIR LAUNCHER (FAST MODE)
cd /d "%~dp0"

:: ==============================================================
:: CONFIG
:: ==============================================================
set "PROGRESS_STEPS=10"
set "BLOCK=█"
set "LOG_RETENTION_DAYS=7"

:: ==============================================================
:: COLORS
:: ==============================================================
set "CLR_BOOT=0B"
set "CLR_OK=0A"
set "CLR_WARN=0E"
set "CLR_ERR=0C"
set "CLR_AI=09"

:: ==============================================================
:: POWERSHELL
:: ==============================================================
where powershell >nul 2>&1 && (set "HAVE_PS=1") || (set "HAVE_PS=0")

:: ==============================================================
:: TIMESTAMP
:: ==============================================================
for /f "usebackq delims=" %%I in (`
  powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"
`) do set "TS=%%~I"

:: ==============================================================
:: LOGGING
:: ==============================================================
set "LOG_DIR=%~dp0logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\launcher_%TS%.log"
forfiles /P "%LOG_DIR%" /M *.log /D -%LOG_RETENTION_DAYS% /C "cmd /c del /q @path" >nul 2>&1

:: ==============================================================
:: PYTHON DETECTION
:: ==============================================================
set "PYTHON_CMD="
for %%P in ("python" "py -3" "py") do (
  if not defined PYTHON_CMD (
    %%~P -c "import sys" >nul 2>&1 && set "PYTHON_CMD=%%~P"
  )
)

if not defined PYTHON_CMD (
  color %CLR_ERR%
  echo [FAIL] Python not found.
  pause
  exit /b 1
)

:: ==============================================================
:: APP AUTO-DETECT
:: ==============================================================
set "APP_FILE="
for %%F in (
  mantis_studio_fixed.py
  mantis_studio.py
  Mantis_Studio_v45_2.py
  app.py
) do (
  if not defined APP_FILE if exist "%%~F" set "APP_FILE=%%~F"
)

if not defined APP_FILE (
  color %CLR_ERR%
  echo [FAIL] No MANTIS app file found.
  pause
  exit /b 1
)

:: ==============================================================
:: MENU
:: ==============================================================
:menu
cls
call :banner
color %CLR_BOOT%
echo.
echo   ACTIVE APP : %APP_FILE%
echo   PYTHON     : %PYTHON_CMD%
echo   LOG FILE   : %LOG_FILE%
echo.
echo ----------------------------------------------------------
echo   1) Launch MANTIS (cinematic fast)
echo   2) Diagnostics and Repair
echo   3) Install or Update Dependencies
echo   4) Choose App File
echo   0) Exit
echo ----------------------------------------------------------
echo.
choice /c 12340 /n /m "Select: "

set "CHOICE=%ERRORLEVEL%"

if "%CHOICE%"=="1" goto launch
if "%CHOICE%"=="2" goto diag
if "%CHOICE%"=="3" goto deps
if "%CHOICE%"=="4" goto choose
if "%CHOICE%"=="5" goto end
goto menu


:: ==============================================================
:: LAUNCH
:: ==============================================================
:launch
cls
call :banner
color %CLR_BOOT%

echo.
echo   Awakening MANTIS Neural Interface...
call :sleep 140
echo.

echo   Synchronizing Core Frequencies...
call :progress_bar_fast
echo.

echo   Establishing Secure Runtime Channel...
call :progress_bar_fast
echo.
cls
color %CLR_WARN%
call :banner
echo.
echo Verifying dependencies...
for %%D in (streamlit requests python-dotenv weasyprint reportlab pandas) do (
  %PYTHON_CMD% -m pip show %%D >nul 2>&1
  if errorlevel 1 (
    color %CLR_WARN%
    echo Installing %%D...
    call :progress_bar_fast
    %PYTHON_CMD% -m pip install %%D --quiet >>"%LOG_FILE%" 2>&1
  ) else (
    color %CLR_OK%
    echo OK: %%D
  )
)

:: ---- QUIET AI PROBE ----
set "AI_READY=0"
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command ^
    "try{(Invoke-WebRequest 'http://localhost:11434/api/tags' -TimeoutSec 2).StatusCode}catch{0}" >"%TEMP%\oll_launch.txt"
)
set /p OLLAMA=<"%TEMP%\oll_launch.txt"
del "%TEMP%\oll_launch.txt" >nul 2>&1
if "%OLLAMA%"=="200" set "AI_READY=1"

call :banner
echo.
color %CLR_BOOT%
echo   Initializing Neural Network...
echo.
set "bar="
for /L %%i in (1,1,10) do (
    set "bar=!bar!%BLOCK%"
    <nul set /p ="   !bar!"
    powershell -Command "Start-Sleep -Milliseconds 25"
    echo.
)

echo Neural Network Online!
powershell -Command "Start-Sleep -Milliseconds 25"
echo.
echo Connecting to Neural Network
for /L %%i in (1,1,10) do (
    <nul set /p ="..."
    powershell -Command "Start-Sleep -Milliseconds 50"
)
echo.
echo Connected!
powershell -Command "Start-Sleep -Milliseconds 100"


)
call :banner
if "%AI_READY%"=="1" (
  color %CLR_AI%
  echo.
  echo ================================
  echo   MANTIS A.I. ONLINE
  echo ================================
) else (
  color %CLR_WARN%
  echo.
  echo AI Core Offline - Safe Mode
)
call :sleep 120

echo Launching MANTIS Studio...

start "" "http://localhost:8501"
%PYTHON_CMD% -m streamlit run "%APP_FILE%" --server.headless true >>"%LOG_FILE%" 2>&1

pause
goto menu

:: ==============================================================
:: DIAGNOSTICS
:: ==============================================================
:diag
cls
call :banner
color %CLR_WARN%

set "DIAG_FILE=%LOG_DIR%\diagnostics_%TS%.txt"
echo MANTIS SYSTEM DIAGNOSTICS >"%DIAG_FILE%"
echo Timestamp: %TS%>>"%DIAG_FILE%"
echo.>>"%DIAG_FILE%"

call :diag_system
call :diag_streamlit
call :diag_ports

notepad "%DIAG_FILE%"

echo --------------------------------------------------
echo   F) Fix and Relaunch
echo   B) Back to menu
echo --------------------------------------------------
choice /c FB /n /m "Select: "

set "DCHOICE=%ERRORLEVEL%"

if "%DCHOICE%"=="1" goto diag_fix
if "%DCHOICE%"=="2" goto menu
goto menu

:: ==============================================================
:: FIX AND RELAUNCH
:: ==============================================================
:diag_fix
cls
call :banner
color %CLR_WARN%
echo Fixing common issues...

%PYTHON_CMD% -m pip install --upgrade pip >>"%DIAG_FILE%" 2>&1
for %%D in (streamlit requests pandas python-dotenv weasyprint reportlab) do (
  %PYTHON_CMD% -m pip show %%D >nul 2>&1 || (
    %PYTHON_CMD% -m pip install %%D >>"%DIAG_FILE%" 2>&1
  )
)

color %CLR_OK%
echo Fix complete. Relaunching...
call :sleep 120
goto launch

:: ==============================================================
:: DIAG HELPERS
:: ==============================================================
:diag_system
echo [SYSTEM]
%PYTHON_CMD% --version >>"%DIAG_FILE%"
echo PASS Python OK
echo PASS Python OK>>"%DIAG_FILE%"
echo.
exit /b

:diag_streamlit
echo [STREAMLIT]
%PYTHON_CMD% -c "import streamlit" >nul 2>&1 && (
  echo PASS Streamlit import
  echo PASS Streamlit import>>"%DIAG_FILE%"
) || (
  echo FAIL Streamlit import
  echo FAIL Streamlit import>>"%DIAG_FILE%"
)
echo.
exit /b

:diag_ports
echo [PORTS]
%PYTHON_CMD% -c "import socket; s=socket.socket(); s.bind(('',8501)); s.close()" >nul 2>&1 && (
  echo PASS Port 8501 free
  echo PASS Port 8501 free>>"%DIAG_FILE%"
) || (
  echo WARN Port 8501 in use
  echo WARN Port 8501 in use>>"%DIAG_FILE%"
)
echo.
exit /b

:: ==============================================================
:: DEPS
:: ==============================================================
:deps
cls
call :banner
color %CLR_WARN%
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install --upgrade streamlit requests pandas
pause
goto menu

:: ==============================================================
:: CHOOSE APP
:: ==============================================================
:choose
cls
call :banner
color %CLR_BOOT%
echo Enter filename:
set /p NEWAPP=File: 
if exist "%NEWAPP%" (
  set "APP_FILE=%NEWAPP%"
  color %CLR_OK%
  echo Selected %APP_FILE%
) else (
  color %CLR_ERR%
  echo File not found.
)
pause
goto menu

:: ==============================================================
:: HELPERS
:: ==============================================================
:progress_bar_fast
setlocal EnableDelayedExpansion
set "bar="
set "spaces=.........."
for /L %%i in (1,1,%PROGRESS_STEPS%) do (
  set "bar=!bar!%BLOCK%"
  set "rest=!spaces:~%%i!"
  <nul set /p ="   [!bar!!rest!]"
  call :sleep 15
  echo/
)
endlocal & exit /b

:sleep
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "Start-Sleep -Milliseconds %~1" >nul 2>&1
) else (
  ping 127.0.0.1 -n 2 >nul
)
exit /b

:: ==============================================================
:: BANNER
:: ==============================================================
:banner
cls
echo.
echo  ╔═══════════════════════════════════════════════════════════════╗
echo  ║                                                               ║
echo  ║       ███╗   ███╗ █████╗ ███╗   ██╗████████╗██╗███████╗       ║
echo  ║       ████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██║██╔════╝       ║
echo  ║       ██ ████ ██║███████║██ ██╗ ██║   ██║   ██║██║            ║
echo  ║       ██╔████╔██║███████║██╔╗██ ██║   ██║   ██║███████╗       ║
echo  ║       ██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██║╚════██║       ║
echo  ║       ██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ██║     ██║       ║
echo  ║       ██║     ██║██║  ██║██║  ╚███║   ██║   ██║███████║       ║
echo  ║                                                               ║
echo  ║         Modular AI Narrative Text Intelligence System         ║
echo  ╚═══════════════════════════════════════════════════════════════╝
exit /b

:end
endlocal
exit /b

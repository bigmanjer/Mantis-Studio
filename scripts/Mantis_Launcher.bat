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
set "LOG_FILE=%LOG_DIR%\\launcher_%TS%.log"
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
  app/main.py
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
:: LAUNCH
:: ============================================================== 
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

for %%D in (
  streamlit
  requests
  python-dotenv
  weasyprint
  reportlab
  pandas
  numpy
  pytz
  Pillow
  matplotlib
  tqdm
) do (
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

echo.
color %CLR_OK%
echo Dependencies are good!
call :sleep 1500

:: ---- QUIET AI PROBE ----
set "AI_READY=0"
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command ^
    "try{(Invoke-WebRequest 'http://localhost:11434/api/tags' -TimeoutSec 2).StatusCode}catch{0}" >"%TEMP%\\oll_launch.txt"
)
set /p OLLAMA=<"%TEMP%\\oll_launch.txt"
del "%TEMP%\\oll_launch.txt" >nul 2>&1
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
exit /b

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

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
set "SERVER_PORT=8501"
set "APP_URL=http://localhost:%SERVER_PORT%"

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
set "STREAMLIT_LOG_FILE=%LOG_DIR%\\streamlit_%TS%.log"
set "CHAT_LOG_FILE=%LOG_DIR%\\chat_%TS%.log"
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
  python-docx
  pypdf
  weasyprint
  reportlab
  pandas
  plotly
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
set "AI_READY=1"
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

call :start_mantis_server
start "" "%APP_URL%"
call :mantis_chat

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
:: MANTIS RUNTIME
:: ==============================================================

:start_mantis_server
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$py = '%PYTHON_CMD%'; $app = '%APP_FILE%'; $port = '%SERVER_PORT%'; $log = '%STREAMLIT_LOG_FILE%'; $cmd = ('/c {0} -m streamlit run \"{1}\" --server.headless true --server.port {2} >> \"{3}\" 2>&1' -f $py, $app, $port, $log); Start-Process -WindowStyle Hidden -FilePath 'cmd.exe' -ArgumentList $cmd" >nul 2>&1
) else (
  start "MANTIS Streamlit Server" /min cmd /c ""%PYTHON_CMD%" -m streamlit run "%APP_FILE%" --server.headless true --server.port %SERVER_PORT% >> "%STREAMLIT_LOG_FILE%" 2>&1"
)
exit /b

:mantis_chat
set "MANTIS_CHATBOT=scripts\mantis_launcher_chat.py"
if exist "%MANTIS_CHATBOT%" (
  %PYTHON_CMD% "%MANTIS_CHATBOT%" --url "%APP_URL%" --port "%SERVER_PORT%" --log-file "%STREAMLIT_LOG_FILE%" --chat-log-file "%CHAT_LOG_FILE%" --repo-root "%CD%"
  if not errorlevel 1 exit /b
  echo MANTIS Python chat failed to start. Falling back to basic launcher chat.>>"%CHAT_LOG_FILE%"
  echo MANTIS Python chat failed to start. Falling back to basic launcher chat.
  pause
)
color %CLR_AI%
call :banner
echo.
echo ======================================
echo   TALK TO MANTIS
echo ======================================
echo.
echo   MANTIS Studio is running at %APP_URL%
echo   Python chat did not start, so this is fallback mode.
echo   Type /help for commands.
echo.

:mantis_chat_loop
set "MANTIS_INPUT="
set /p "MANTIS_INPUT=  You > "
if not defined MANTIS_INPUT goto mantis_chat_loop
set "MANTIS_CMD=%MANTIS_INPUT%"

if /i "%MANTIS_CMD%"=="/restart" goto mantis_restart
if /i "%MANTIS_CMD%"=="/relaunch" goto mantis_restart
if /i "%MANTIS_CMD%"=="/reload" goto mantis_restart
if /i "%MANTIS_CMD%"=="/open" goto mantis_open
if /i "%MANTIS_CMD%"=="/status" goto mantis_status
if /i "%MANTIS_CMD%"=="/log" goto mantis_log
if /i "%MANTIS_CMD%"=="/logs" goto mantis_log
if /i "%MANTIS_CMD%"=="/help" goto mantis_help
if /i "%MANTIS_CMD%"=="/commands" goto mantis_help
if /i "%MANTIS_CMD%"=="/clear" goto mantis_clear
if /i "%MANTIS_CMD%"=="/cls" goto mantis_clear
if /i "%MANTIS_CMD%"=="/exit" goto mantis_exit
if /i "%MANTIS_CMD%"=="/quit" goto mantis_exit

echo   MANTIS ^> I heard "%MANTIS_INPUT%".
echo   MANTIS ^> Fallback mode only runs slash commands. Try /help.
echo.
goto mantis_chat_loop

:mantis_restart
echo   MANTIS ^> Reopening the localhost window.
start "" "%APP_URL%"
echo   MANTIS ^> If the page is still loading, give the server a few seconds.
echo.
goto mantis_chat_loop

:mantis_open
echo   MANTIS ^> Opening MANTIS Studio.
start "" "%APP_URL%"
echo.
goto mantis_chat_loop

:mantis_status
echo   MANTIS ^> Checking localhost:%SERVER_PORT%...
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "$ok = Test-NetConnection -ComputerName 'localhost' -Port %SERVER_PORT% -InformationLevel Quiet; if ($ok) { '  MANTIS > Runtime channel is online.' } else { '  MANTIS > I cannot see the server yet. Try restart, or check log.' }"
) else (
  netstat -ano | findstr ":%SERVER_PORT%" >nul && echo   MANTIS ^> Runtime channel is online. || echo   MANTIS ^> I cannot see the server yet. Try restart, or check log.
)
echo.
goto mantis_chat_loop

:mantis_log
echo   MANTIS ^> Recent launcher log:
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "if (Test-Path '%LOG_FILE%') { Get-Content '%LOG_FILE%' -Tail 18 } else { '  No log file found yet.' }"
) else (
  type "%LOG_FILE%"
)
echo.
goto mantis_chat_loop

:mantis_help
echo   MANTIS ^> Commands:
echo     /restart   Reopen the localhost browser window.
echo     /open      Open MANTIS Studio.
echo     /status    Check whether localhost:%SERVER_PORT% is responding.
echo     /logs      Show the newest launcher log lines.
echo     /clear     Redraw this chat screen.
echo     /exit      Close this launcher chat. MANTIS Studio keeps running.
echo.
goto mantis_chat_loop

:mantis_clear
goto mantis_chat

:mantis_exit
echo   MANTIS ^> Closing launcher chat. Your MANTIS server may keep running in the background.
echo.
pause
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
echo  ║       ██║     ██║██║  ██║██║  ████║   ██║   ██║███████║       ║
echo  ║       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚══════╝       ║
echo  ║         Modular AI Narrative Text Intelligence System         ║
echo  ╚═══════════════════════════════════════════════════════════════╝
exit /b

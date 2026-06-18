@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
title MANTIS STUDIO
cd /d "%~dp0"

:: ============================================================== 
:: CONFIG
:: ============================================================== 
set "PROGRESS_STEPS=10"
set "BLOCK=█"
set "BLOCK=#"
set "LOG_RETENTION_DAYS=7"
set "SERVER_PORT=8501"
set "APP_URL=http://localhost:%SERVER_PORT%"
set "HEALTH_URL=http://127.0.0.1:%SERVER_PORT%"

:: ============================================================== 
:: COLORS
:: ============================================================== 
set "CLR_BOOT=0E"
set "CLR_OK=0A"
set "CLR_WARN=0E"
set "CLR_ERR=0C"
set "CLR_AI=0A"
set "CLR_CHAT=0A"

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
set "STREAMLIT_LOG_FILE=%LOG_DIR%\streamlit_%TS%.log"
set "CHAT_LOG_FILE=%LOG_DIR%\chat_%TS%.log"
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
  echo [FAIL] PYTHON NOT FOUND.
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
  echo [FAIL] NO MANTIS APP FILE FOUND.
  pause
  exit /b 1
)

:: ============================================================== 
:: LAUNCH
:: ============================================================== 
cls
color %CLR_WARN%
call :banner

echo.
echo   AWAKENING MANTIS NEURAL INTERFACE...
call :sleep 140
echo.

echo   SYNCHRONIZING CORE FREQUENCIES...
echo.
call :progress_bar_fast
color %CLR_OK%
echo   CORE FREQUENCIES SYNCHRONIZED.
call :sleep 450
color %CLR_WARN%
echo.

echo   ESTABLISHING SECURE RUNTIME CHANNEL...
echo.
call :progress_bar_fast
color %CLR_OK%
echo   RUNTIME CHANNEL STAGED.
call :sleep 450
color %CLR_WARN%
echo.
cls
color %CLR_WARN%
call :banner
echo.
echo VERIFYING DEPENDENCIES...

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
  playwright
) do (
  %PYTHON_CMD% -m pip show %%D >nul 2>&1
  if errorlevel 1 (
    color %CLR_WARN%
    echo INSTALLING %%D...
    echo.
    call :progress_bar_fast
    %PYTHON_CMD% -m pip install %%D --quiet >>"%LOG_FILE%" 2>&1
    if errorlevel 1 (
      color %CLR_ERR%
      echo [FAIL] COULD NOT INSTALL %%D.
      echo Check "%LOG_FILE%" for details.
      pause
      exit /b 1
    )
    color %CLR_OK%
    echo OK: %%D
    call :sleep 90
    color %CLR_WARN%
  ) else (
    color %CLR_OK%
    echo OK: %%D
    call :sleep 90
    color %CLR_WARN%
  )
)

echo.
color %CLR_OK%
echo DEPENDENCIES ARE GOOD!
call :sleep 1500

:: ---- QUIET AI PROBE ----
set "AI_READY=1"
color %CLR_WARN%
call :banner
echo.
color %CLR_WARN%
echo   INITIALIZING NEURAL NETWORK...
echo.
call :progress_bar_neural

echo.
color %CLR_OK%
echo NEURAL NETWORK ONLINE!
call :sleep 450
color %CLR_WARN%
echo.
echo CONNECTING TO NEURAL NETWORK...
echo.
call :progress_bar_neural

echo.
color %CLR_OK%
echo CONNECTED!
call :sleep 650
color %CLR_WARN%

if "%AI_READY%"=="1" (
  color %CLR_AI%
  call :banner
  echo.
  echo ================================
  echo   MANTIS A.I. ONLINE
  echo ================================
) else (
  color %CLR_ERR%
  call :banner
  echo.
  echo AI CORE OFFLINE - SAFE MODE
)
call :sleep 120

color %CLR_WARN%
echo.
echo   STARTING MANTIS LOCAL SERVER...
call :start_mantis_server
call :wait_for_server
if errorlevel 1 (
  color %CLR_ERR%
  echo.
  echo [FAIL] MANTIS STUDIO DID NOT ANSWER ON %APP_URL%.
  echo Check "%STREAMLIT_LOG_FILE%" for details.
  if "%HAVE_PS%"=="1" (
    echo.
    echo Recent runtime log:
    powershell -NoProfile -Command "if (Test-Path '%STREAMLIT_LOG_FILE%') { Get-Content '%STREAMLIT_LOG_FILE%' -Tail 12 }"
  )
  pause
  exit /b 1
)
color %CLR_OK%
echo.
echo   RUNTIME VERIFIED: %APP_URL%
call :sleep 650
start "" "%APP_URL%"
call :mantis_chat

exit /b

:: ============================================================== 
:: HELPERS
:: ============================================================== 
:progress_bar_fast
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "$full=[string][char]0x2588; $empty=[string][char]0x2591; for($i=1; $i -le %PROGRESS_STEPS%; $i++){ $bar=($full * $i) + ($empty * (%PROGRESS_STEPS% - $i)); [Console]::Write([char]13 + '   [' + $bar + ']'); Start-Sleep -Milliseconds 80 }; Write-Host ''"
  exit /b
)
setlocal EnableDelayedExpansion
for /f %%a in ('copy /Z "%~dpf0" nul') do set "CR=%%a"
set "spaces=░░░░░░░░░░"
set "spaces=----------"
set "bar="
for /L %%i in (1,1,%PROGRESS_STEPS%) do (
  set "bar=!bar!%BLOCK%"
  set "rest=!spaces:~%%i!"
  <nul set /p ="!CR!   [!bar!!rest!]"
  call :sleep 80
)
echo.
endlocal & exit /b

:progress_bar_neural
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "$full=[string][char]0x2588; $empty=[string][char]0x2591; for($i=1; $i -le %PROGRESS_STEPS%; $i++){ $bar=($full * $i) + ($empty * (%PROGRESS_STEPS% - $i)); [Console]::Write([char]13 + '   [' + $bar + ']'); Start-Sleep -Milliseconds 220 }; Write-Host ''"
  exit /b
)
setlocal EnableDelayedExpansion
for /f %%a in ('copy /Z "%~dpf0" nul') do set "CR=%%a"
set "spaces=░░░░░░░░░░"
set "spaces=----------"
set "bar="
for /L %%i in (1,1,%PROGRESS_STEPS%) do (
  set "bar=!bar!%BLOCK%"
  set "rest=!spaces:~%%i!"
  <nul set /p ="!CR!   [!bar!!rest!]"
  call :sleep 220
)
echo.
endlocal & exit /b

:sleep
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "Start-Sleep -Milliseconds %~1" >nul 2>&1
) else (
  ping 127.0.0.1 -n 2 >nul
)
exit /b

:wait_for_server
color %CLR_WARN%
echo.
echo   VERIFYING LOCAL RUNTIME...
for /L %%i in (1,1,90) do (
  if "%HAVE_PS%"=="1" (
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri '%HEALTH_URL%' -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } } catch { try { $c = New-Object Net.Sockets.TcpClient; $iar = $c.BeginConnect('127.0.0.1', %SERVER_PORT%, $null, $null); if ($iar.AsyncWaitHandle.WaitOne(700) -and $c.Connected) { $c.Close(); exit 0 }; $c.Close() } catch {}; exit 1 }; exit 1" >nul 2>&1
    if not errorlevel 1 exit /b 0
  ) else (
    netstat -ano | findstr ":%SERVER_PORT%" >nul && exit /b 0
  )
  <nul set /p ="."
  call :sleep 500
)
echo.
exit /b 1

:: ==============================================================
:: MANTIS RUNTIME
:: ==============================================================

:start_mantis_server
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri '%HEALTH_URL%' -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } } catch { exit 1 }" >nul 2>&1
  if not errorlevel 1 (
    echo   EXISTING MANTIS RUNTIME DETECTED ON %APP_URL%.
    exit /b 0
  )
) else (
  netstat -ano | findstr ":%SERVER_PORT%" >nul && exit /b 0
)
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$py = '%PYTHON_CMD%'; $app = '%APP_FILE%'; $port = '%SERVER_PORT%'; $log = '%STREAMLIT_LOG_FILE%'; $cmd = ('/c {0} -m streamlit run \"{1}\" --server.headless true --server.port {2} >> \"{3}\" 2>&1' -f $py, $app, $port, $log); Start-Process -WindowStyle Hidden -FilePath 'cmd.exe' -ArgumentList $cmd" >nul 2>&1
) else (
  start "MANTIS Streamlit Server" /min cmd /c ""%PYTHON_CMD%" -m streamlit run "%APP_FILE%" --server.headless true --server.port %SERVER_PORT% >> "%STREAMLIT_LOG_FILE%" 2>&1"
)
exit /b

:mantis_chat
color %CLR_CHAT%
set "MANTIS_CHATBOT=scripts\mantis_launcher_chat.py"
if exist "%MANTIS_CHATBOT%" (
  %PYTHON_CMD% "%MANTIS_CHATBOT%" --url "%APP_URL%" --port "%SERVER_PORT%" --log-file "%STREAMLIT_LOG_FILE%" --chat-log-file "%CHAT_LOG_FILE%" --repo-root "%CD%" --handoff
  if not errorlevel 1 exit /b
  echo MANTIS PYTHON CHAT FAILED TO START. FALLING BACK TO BASIC LAUNCHER CHAT.>>"%CHAT_LOG_FILE%"
  echo MANTIS PYTHON CHAT FAILED TO START. FALLING BACK TO BASIC LAUNCHER CHAT.
  pause
)
color %CLR_ERR%
echo.
echo   [RUNTIME ] %APP_URL%
echo   [HELP    ] TYPE /help FOR COMMANDS. EVERYTHING ELSE IS CONVERSATION.
echo.
echo   PYTHON CHAT DID NOT START, SO THIS IS FALLBACK MODE.
echo.

:mantis_chat_loop
set "MANTIS_INPUT="
set /p "MANTIS_INPUT=  YOU > "
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

echo   MANTIS ^> I HEARD "%MANTIS_INPUT%".
echo   MANTIS ^> FALLBACK MODE ONLY RUNS SLASH COMMANDS. TRY /help.
echo.
goto mantis_chat_loop

:mantis_restart
echo   MANTIS ^> REOPENING THE LOCALHOST WINDOW.
start "" "%APP_URL%"
echo   MANTIS ^> IF THE PAGE IS STILL LOADING, GIVE THE SERVER A FEW SECONDS.
echo.
goto mantis_chat_loop

:mantis_open
echo   MANTIS ^> OPENING MANTIS STUDIO.
start "" "%APP_URL%"
echo.
goto mantis_chat_loop

:mantis_status
color %CLR_WARN%
echo   MANTIS ^> CHECKING LOCALHOST:%SERVER_PORT%...
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "if (Test-NetConnection -ComputerName 'localhost' -Port %SERVER_PORT% -InformationLevel Quiet) { exit 0 } else { exit 1 }" >nul 2>&1
  if errorlevel 1 (
    color %CLR_ERR%
    echo   MANTIS ^> I CANNOT SEE THE SERVER YET. TRY /restart, OR CHECK /logs.
  ) else (
    color %CLR_OK%
    echo   MANTIS ^> RUNTIME CHANNEL IS ONLINE.
  )
) else (
  netstat -ano | findstr ":%SERVER_PORT%" >nul
  if errorlevel 1 (
    color %CLR_ERR%
    echo   MANTIS ^> I CANNOT SEE THE SERVER YET. TRY /restart, OR CHECK /logs.
  ) else (
    color %CLR_OK%
    echo   MANTIS ^> RUNTIME CHANNEL IS ONLINE.
  )
)
echo.
color %CLR_CHAT%
goto mantis_chat_loop

:mantis_log
echo   MANTIS ^> RECENT LAUNCHER LOG:
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "if (Test-Path '%LOG_FILE%') { Get-Content '%LOG_FILE%' -Tail 18 } else { '  NO LOG FILE FOUND YET.' }"
) else (
  type "%LOG_FILE%"
)
echo.
goto mantis_chat_loop

:mantis_help
echo   MANTIS ^> COMMANDS:
echo     /restart   REOPEN THE LOCALHOST BROWSER WINDOW.
echo     /open      OPEN MANTIS STUDIO.
echo     /status    CHECK WHETHER LOCALHOST:%SERVER_PORT% IS RESPONDING.
echo     /logs      SHOW THE NEWEST LAUNCHER LOG LINES.
echo     /clear     REDRAW THIS CHAT SCREEN.
echo     /exit      CLOSE THIS LAUNCHER CHAT. MANTIS STUDIO KEEPS RUNNING.
echo.
goto mantis_chat_loop

:mantis_clear
goto mantis_chat

:mantis_exit
echo   MANTIS ^> CLOSING LAUNCHER CHAT. YOUR MANTIS SERVER MAY KEEP RUNNING IN THE BACKGROUND.
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
echo  ║         MODULAR AI NARRATIVE TEXT INTELLIGENCE SYSTEM         ║
echo  ╚═══════════════════════════════════════════════════════════════╝
exit /b

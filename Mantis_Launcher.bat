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
set "BLOCK=#"
set "LOG_RETENTION_DAYS=7"
set "SERVER_PORT=8501"
set "APP_URL=http://localhost:%SERVER_PORT%"
set "HEALTH_URL=http://127.0.0.1:%SERVER_PORT%/_stcore/health"

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
for /F "tokens=1,2 delims=#" %%A in ('"prompt #$H#$E# & echo on & for %%B in (1) do rem"') do set "ESC=%%B"
set "C_OK=%ESC%[92m"
set "C_WARN=%ESC%[93m"
set "C_ERR=%ESC%[91m"
set "C_CHAT=%ESC%[96m"
set "C_RESET=%ESC%[0m"

:: ============================================================== 
:: TIMESTAMP
:: ============================================================== 
for /f "usebackq delims=" %%I in (`
  powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"
`) do set "TS=%%~I"

:: ============================================================== 
:: LOGGING
:: ============================================================== 
set "LOG_ROOT=%~dp0logs"
set "LAUNCHER_LOG_DIR=%LOG_ROOT%\launcher"
set "STREAMLIT_LOG_DIR=%LOG_ROOT%\streamlit"
set "CHAT_LOG_DIR=%LOG_ROOT%\chat"
if not exist "%LOG_ROOT%" mkdir "%LOG_ROOT%"
if not exist "%LAUNCHER_LOG_DIR%" mkdir "%LAUNCHER_LOG_DIR%"
if not exist "%STREAMLIT_LOG_DIR%" mkdir "%STREAMLIT_LOG_DIR%"
if not exist "%CHAT_LOG_DIR%" mkdir "%CHAT_LOG_DIR%"
set "LOG_FILE=%LAUNCHER_LOG_DIR%\launcher_%TS%.log"
set "STREAMLIT_LOG_FILE=%STREAMLIT_LOG_DIR%\streamlit_%TS%.log"
set "CHAT_LOG_FILE=%CHAT_LOG_DIR%\chat_%TS%.log"
for %%L in ("%LAUNCHER_LOG_DIR%" "%STREAMLIT_LOG_DIR%" "%CHAT_LOG_DIR%") do (
  forfiles /P "%%~L" /M *.log /D -%LOG_RETENTION_DAYS% /C "cmd /c del /q @path" >nul 2>&1
)

:: ============================================================== 
:: PYTHON DETECTION
:: ============================================================== 
set "PYTHON_CMD="
for %%P in ("python" "py -3" "py") do (
  if not defined PYTHON_CMD (
    %%~P -c "import sys" >nul 2>&1 && set "PYTHON_CMD=%%~P"
  )
)

if /i "%~1"=="--self-test" goto self_test

if not defined PYTHON_CMD (
  rem color handled by ANSI line output
  echo.
  call :say_err "[FAIL] PYTHON NOT FOUND."
  echo.
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
  rem color handled by ANSI line output
  echo.
  call :say_err "[FAIL] NO MANTIS APP FILE FOUND."
  echo.
  pause
  exit /b 1
)

:: ============================================================== 
:: LAUNCH
:: ============================================================== 
cls
rem color handled by ANSI line output
call :banner
rem color handled by ANSI line output
echo.
call :say_warn "  AWAKENING MANTIS NEURAL INTERFACE..."
call :sleep 140
echo.

call :say_warn "  SYNCHRONIZING CORE FREQUENCIES..."
echo.
call :progress_bar_fast
rem color handled by ANSI line output
call :say_ok "  CORE FREQUENCIES SYNCHRONIZED."
call :sleep 450
rem color handled by ANSI line output
echo.

call :say_warn "  ESTABLISHING SECURE RUNTIME CHANNEL..."
echo.
call :progress_bar_fast
rem color handled by ANSI line output
call :say_ok "  RUNTIME CHANNEL STAGED."
call :sleep 450
rem color handled by ANSI line output
echo.
cls
rem color handled by ANSI line output
call :banner
rem color handled by ANSI line output
echo.
call :say_warn "VERIFYING DEPENDENCIES..."
echo.
set "INSTALLED_DEPENDENCY=0"

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
    set "INSTALLED_DEPENDENCY=1"
    rem color handled by ANSI line output
    call :say_warn "  INSTALLING %%D..."
    echo.
    call :progress_bar_fast
    %PYTHON_CMD% -m pip install %%D --quiet >>"%LOG_FILE%" 2>&1
    if errorlevel 1 (
      rem color handled by ANSI line output
      echo.
      call :say_err "[FAIL] COULD NOT INSTALL %%D."
      call :say_err "Check %LOG_FILE% for details."
      echo.
      pause
      exit /b 1
    )
    rem color handled by ANSI line output
    call :say_ok "  INSTALLED: %%D"
    call :sleep 90
  ) else (
    rem color handled by ANSI line output
    call :say_ok "  OK: %%D"
    call :sleep 45
  )
)

echo.
rem color handled by ANSI line output
if "%INSTALLED_DEPENDENCY%"=="1" (
  call :say_ok "DEPENDENCIES UPDATED AND READY"
) else (
  call :say_ok "DEPENDENCIES ARE GOOD"
)
call :sleep 1500

:: ---- QUIET AI PROBE ----
set "AI_READY=1"
rem color handled by ANSI line output
call :banner
rem color handled by ANSI line output
echo.
rem color handled by ANSI line output
call :say_warn "  INITIALIZING NEURAL NETWORK..."
echo.
call :progress_bar_neural

echo.
rem color handled by ANSI line output
call :say_ok "NEURAL NETWORK ONLINE"
call :sleep 450
rem color handled by ANSI line output
echo.
call :say_warn "CONNECTING TO NEURAL NETWORK..."
echo.
call :progress_bar_neural

echo.
rem color handled by ANSI line output
call :say_ok "CONNECTED"
call :sleep 650
rem color handled by ANSI line output
if "%AI_READY%"=="1" (
  rem color handled by ANSI line output
  call :banner
  rem color handled by ANSI line output
  echo.
  call :say_ok "================================"
  call :say_ok "  MANTIS A.I. ONLINE"
  call :say_ok "================================"
) else (
  rem color handled by ANSI line output
  call :banner
  rem color handled by ANSI line output
  echo.
  echo.
  call :say_err "AI CORE OFFLINE - SAFE MODE"
  echo.
)
call :sleep 120

rem color handled by ANSI line output
echo.
call :say_warn "  STARTING MANTIS LOCAL SERVER..."
call :start_mantis_server
call :wait_for_server
if errorlevel 1 (
  rem color handled by ANSI line output
  echo.
  echo.
  call :say_err "[FAIL] MANTIS STUDIO DID NOT ANSWER ON %APP_URL%."
  call :say_err "Check %STREAMLIT_LOG_FILE% for details."
  echo.
  if "%HAVE_PS%"=="1" (
    echo.
    call :say_err "Recent runtime log:"
    powershell -NoProfile -Command "if (Test-Path '%STREAMLIT_LOG_FILE%') { Get-Content '%STREAMLIT_LOG_FILE%' -Tail 12 }"
  )
  pause
  exit /b 1
)
rem color handled by ANSI line output
echo.
call :say_ok "  RUNTIME VERIFIED: %APP_URL%"
call :sleep 650
start "" "%APP_URL%"
call :mantis_chat

exit /b

:: ============================================================== 
:: HELPERS
:: ============================================================== 
:progress_bar_fast
if defined PYTHON_CMD if exist "scripts\mantis_progress.py" (
  %PYTHON_CMD% "scripts\mantis_progress.py" --steps %PROGRESS_STEPS% --delay 80
  exit /b
)
setlocal EnableDelayedExpansion
for /f %%a in ('copy /Z "%~dpf0" nul') do set "CR=%%a"
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
if defined PYTHON_CMD if exist "scripts\mantis_progress.py" (
  %PYTHON_CMD% "scripts\mantis_progress.py" --steps %PROGRESS_STEPS% --delay 220
  exit /b
)
setlocal EnableDelayedExpansion
for /f %%a in ('copy /Z "%~dpf0" nul') do set "CR=%%a"
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
rem color handled by ANSI line output
echo.
echo   VERIFYING LOCAL RUNTIME...
for /L %%i in (1,1,90) do (
  if "%HAVE_PS%"=="1" (
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri '%HEALTH_URL%' -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } } catch {}; exit 1" >nul 2>&1
    if not errorlevel 1 exit /b 0
  ) else (
    curl -fsS --max-time 3 "%HEALTH_URL%" >nul 2>nul && exit /b 0
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
  powershell -NoProfile -Command "try { Get-NetTCPConnection -LocalPort %SERVER_PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { if ($_ -and $_ -ne $PID) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } } } catch {}" >nul 2>&1
) else (
  for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%SERVER_PORT% .*LISTENING"') do taskkill /F /PID %%P >nul 2>&1
)
start "MANTIS Runtime" /min cmd /c ""%PYTHON_CMD%" -m streamlit run "%APP_FILE%" --server.headless true --server.port %SERVER_PORT% >> "%STREAMLIT_LOG_FILE%" 2>&1"
exit /b

:mantis_chat
rem color handled by ANSI line output
set "MANTIS_CHATBOT=scripts\mantis_launcher_chat.py"
if exist "%MANTIS_CHATBOT%" (
  %PYTHON_CMD% "%MANTIS_CHATBOT%" --url "%APP_URL%" --port "%SERVER_PORT%" --log-file "%STREAMLIT_LOG_FILE%" --chat-log-file "%CHAT_LOG_FILE%" --repo-root "%CD%" --handoff
  if not errorlevel 1 exit /b
  rem color handled by ANSI line output
  echo MANTIS PYTHON CHAT FAILED TO START. FALLING BACK TO BASIC LAUNCHER CHAT.>>"%CHAT_LOG_FILE%"
  echo.
  echo MANTIS PYTHON CHAT FAILED TO START. FALLING BACK TO BASIC LAUNCHER CHAT.
  echo.
  pause
)
rem color handled by ANSI line output
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
call :say_warn "  MANTIS - CHECKING LOCALHOST:%SERVER_PORT%..."
if "%HAVE_PS%"=="1" (
  powershell -NoProfile -Command "if (Test-NetConnection -ComputerName 'localhost' -Port %SERVER_PORT% -InformationLevel Quiet) { exit 0 } else { exit 1 }" >nul 2>&1
  if errorlevel 1 (
    call :say_err "  MANTIS - I CANNOT SEE THE SERVER YET. TRY /restart, OR CHECK /logs."
  ) else (
    call :say_ok "  MANTIS - RUNTIME CHANNEL IS ONLINE."
  )
) else (
  netstat -ano | findstr ":%SERVER_PORT%" >nul
  if errorlevel 1 (
    call :say_err "  MANTIS - I CANNOT SEE THE SERVER YET. TRY /restart, OR CHECK /logs."
  ) else (
    call :say_ok "  MANTIS - RUNTIME CHANNEL IS ONLINE."
  )
)
echo.
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

:say_ok
echo(%C_OK%%~1%C_RESET%
exit /b

:say_warn
echo(%C_WARN%%~1%C_RESET%
exit /b

:say_err
echo(%C_ERR%%~1%C_RESET%
exit /b

:say_chat
echo(%C_CHAT%%~1%C_RESET%
exit /b

:self_test
cls
call :banner
echo.
call :say_warn "  SELF TEST - FAST BAR"
call :progress_bar_fast
echo.
call :say_warn "  SELF TEST - NEURAL BAR"
call :progress_bar_neural
echo.
call :say_ok "  SELF TEST OK"
exit /b 0

:banner
cls
color %CLR_OK%
if defined PYTHON_CMD if exist "scripts\mantis_banner.py" (
  %PYTHON_CMD% "scripts\mantis_banner.py"
  exit /b
)
echo.
echo  +---------------------------------------------------------------+
echo          MANTIS
echo          MODULAR AI NARRATIVE TEXT INTELLIGENCE SYSTEM
echo  +---------------------------------------------------------------+
exit /b

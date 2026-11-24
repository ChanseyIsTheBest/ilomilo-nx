@echo off
rem ilomilo-nx: tools\build_switch_guard.bat with its output in out\<log name> (the copies hooked with their guard forms,
rem app\out\switch-guard), as tools\ilomilo_build_switch.bat does for the everyday build.
rem   tools\ilomilo_build_switch_guard.bat [log name]
setlocal
cd /d "%~dp0.."
set "LOGNAME=%~1"
if "%LOGNAME%"=="" set "LOGNAME=build_switch_guard.log"
call tools\build_switch_guard.bat > "out\%LOGNAME%" 2>&1
set "RC=%ERRORLEVEL%"
echo build_switch_guard exit %RC% >> "out\%LOGNAME%"
exit /b %RC%

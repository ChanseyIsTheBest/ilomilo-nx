@echo off
rem ilomilo-nx: tools\build_switch.bat with its output in out\<log name> (BUILD_DIR / CMAKE_EXTRA / GUARD_FORMS /
rem IN_PLACE as build_switch.bat takes them, from the caller's environment).
rem   tools\ilomilo_build_switch.bat [log name]
setlocal
cd /d "%~dp0.."
set "LOGNAME=%~1"
if "%LOGNAME%"=="" set "LOGNAME=build_switch.log"
call tools\build_switch.bat > "out\%LOGNAME%" 2>&1
set "RC=%ERRORLEVEL%"
echo build_switch exit %RC% >> "out\%LOGNAME%"
exit /b %RC%

@echo off
rem ilomilo-nx: the PC build with Renut's renderer built in, its output in out\build_pc.log.
rem   tools\ilomilo_build_pc.bat [log name]
setlocal
cd /d "%~dp0.."
set "RENUT=ON"
set "LOGNAME=%~1"
if "%LOGNAME%"=="" set "LOGNAME=build_pc.log"
call tools\build_pc.bat > "out\%LOGNAME%" 2>&1
set "RC=%ERRORLEVEL%"
echo build_pc exit %RC% >> "out\%LOGNAME%"
exit /b %RC%

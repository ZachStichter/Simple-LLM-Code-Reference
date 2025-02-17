@echo off
setlocal enabledelayedexpansion
for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq ollama.exe" /fo csv /nh') do (
    set "PID=%%a"
    rem echo Found PID: !PID!
    taskkill /f /pid !PID!
    rem echo Killed process with PID: !PID!
)
endlocal
exit
@echo off
if "%~1"=="" (
    python charts.py --type 1
) else (
    python charts.py --type 1 --file "%~1"
)
pause


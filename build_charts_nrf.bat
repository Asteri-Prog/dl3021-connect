@echo off
if "%~1"=="" (
    python charts.py --type 2
) else (
    python charts.py --type 2 --file "%~1"
)
pause


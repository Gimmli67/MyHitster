@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo Starte MyHitster Generator...
python hitster_generator.py Export/My_80s.csv Export/My_90s.csv Export/My_New_Wave.csv Export/My_Rock.csv
pause

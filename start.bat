@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo Starte MyHitster Generator...
python hitster_generator.py "Playlists/My Hitster Playlist.csv"
pause

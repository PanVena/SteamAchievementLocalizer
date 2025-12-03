@echo off
REM Build script for Windows using Nuitka

echo Building Steam Achievement Localizer for Windows...

REM Get version from the main file
for /f "tokens=3 delims= " %%a in ('findstr "APP_VERSION = " SteamAchievementLocalizer.py') do set VERSION=%%a
set VERSION=%VERSION:"=%

echo Version: %VERSION%

REM Build with Nuitka
python -m nuitka --standalone --onefile ^
  --enable-plugin=pyqt6 ^
  --include-data-dir=assets=assets ^
  --windows-icon-from-ico=assets/icon.ico ^
  --product-name="Steam Achievement Localizer" ^
  --file-version=%VERSION% ^
  --product-version=%VERSION% ^
  --company-name="Vena" ^
  --file-description="Steam Achievement Localizer - Translate game achievements" ^
  --windows-console-mode=disable ^
  --output-filename="SteamAchievementLocalizer.exe" ^
  SteamAchievementLocalizer.py

echo Build complete!
echo Executable: SteamAchievementLocalizer.exe

pause

#!/bin/bash
# Build script for Windows using Nuitka

echo "Building Steam Achievement Localizer for Windows..."

# Get version from the main file
VERSION=$(grep "APP_VERSION = " SteamAchievementLocalizer.py | cut -d'"' -f2)

echo "Version: $VERSION"

# Build with Nuitka
python -m nuitka --standalone --onefile \
  --enable-plugin=pyqt6 \
  --include-data-dir=assets=assets \
  --windows-icon-from-ico=assets/icon.ico \
  --product-name="Steam Achievement Localizer" \
  --file-version="$VERSION" \
  --product-version="$VERSION" \
  --company-name="Vena" \
  --file-description="Steam Achievement Localizer - Translate game achievements" \
  --windows-console-mode=disable \
  --output-filename="SteamAchievementLocalizer.exe" \
  SteamAchievementLocalizer.py

echo "Build complete!"
echo "Executable: SteamAchievementLocalizer.exe"

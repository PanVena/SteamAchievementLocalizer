#!/bin/bash
set -e

echo "========================================="
echo "Steam Achievement Localizer - macOS Build"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get version from source
VERSION=$(grep -oE 'APP_VERSION = "[0-9]+\.[0-9]+\.[0-9]+"' SteamAchievementLocalizer.py | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
echo -e "${GREEN}Version:${NC} $VERSION"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning:${NC} Virtual environment not activated."
    echo "Activating .venv..."
    source .venv/bin/activate
fi

# Check if py2app is installed
if ! python -c "import py2app" 2>/dev/null; then
    echo -e "${YELLOW}py2app not found.${NC} Installing..."
    pip install py2app
fi

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build dist *.spec~ *.egg-info

# Check if icon exists
if [ ! -f "assets/icon.icns" ]; then
    echo -e "${RED}Error:${NC} assets/icon.icns not found!"
    echo "Creating icon from .ico..."

    # Create iconset
    mkdir -p assets/icon.iconset
    sips -s format png assets/icon.ico --out assets/icon.iconset/icon_512x512.png -z 512 512
    sips -s format png assets/icon.ico --out assets/icon.iconset/icon_256x256.png -z 256 256
    sips -s format png assets/icon.ico --out assets/icon.iconset/icon_128x128.png -z 128 128
    sips -s format png assets/icon.ico --out assets/icon.iconset/icon_32x32.png -z 32 32
    sips -s format png assets/icon.ico --out assets/icon.iconset/icon_16x16.png -z 16 16

    # Convert to icns
    iconutil -c icns assets/icon.iconset -o assets/icon.icns
    rm -rf assets/icon.iconset

    echo -e "${GREEN}Icon created successfully!${NC}"
fi

# Build the app
echo ""
echo -e "${GREEN}Building macOS app bundle with py2app...${NC}"
echo ""

python setup.py py2app

# Check if build was successful
if [ ! -d "dist/Steam Achievement Localizer.app" ]; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

# Rename to remove spaces for easier handling
if [ -d "dist/Steam Achievement Localizer.app" ]; then
    mv "dist/Steam Achievement Localizer.app" "dist/SteamAchievementLocalizer.app"
fi

echo ""
echo -e "${GREEN}Build completed successfully!${NC}"
echo ""

# Show app size
APP_SIZE=$(du -sh "dist/SteamAchievementLocalizer.app" | cut -f1)
echo "App size: $APP_SIZE"
echo "Location: $(pwd)/dist/SteamAchievementLocalizer.app"
echo ""

# Ask if user wants to create DMG
read -p "Do you want to create a DMG installer? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    DMG_NAME="SteamAchievementLocalizer-v${VERSION}-macOS.dmg"

    echo ""
    echo -e "${GREEN}Creating DMG...${NC}"

    # Remove old DMG if exists
    rm -f "dist/$DMG_NAME"

    # Create temporary directory for DMG contents
    DMG_DIR="dist/dmg_temp"
    rm -rf "$DMG_DIR"
    mkdir -p "$DMG_DIR"

    # Copy app to temp directory
    cp -R "dist/SteamAchievementLocalizer.app" "$DMG_DIR/"

    # Copy additional files
    cp README.md "$DMG_DIR/" 2>/dev/null || true
    cp LICENSE "$DMG_DIR/" 2>/dev/null || true
    cp CHANGELOG.md "$DMG_DIR/" 2>/dev/null || true

    # Create Applications symlink
    ln -s /Applications "$DMG_DIR/Applications"

    # Create DMG
    hdiutil create -volname "Steam Achievement Localizer v$VERSION" \
        -srcfolder "$DMG_DIR" \
        -ov -format UDZO \
        "dist/$DMG_NAME"

    # Clean up
    rm -rf "$DMG_DIR"

    echo ""
    echo -e "${GREEN}DMG created successfully!${NC}"
    DMG_SIZE=$(du -sh "dist/$DMG_NAME" | cut -f1)
    echo "DMG size: $DMG_SIZE"
    echo "Location: $(pwd)/dist/$DMG_NAME"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Build process complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "To test the app, run:"
echo "  open dist/SteamAchievementLocalizer.app"
echo ""

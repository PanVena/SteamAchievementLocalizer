# Building for macOS

This guide explains how to build Steam Achievement Localizer as a native macOS application.

## Prerequisites

- macOS 10.13 (High Sierra) or later
- Python 3.9 or later
- Virtual environment with dependencies installed

## Quick Build

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run the build script
./build_macos.sh
```

The script will:
- Check and install PyInstaller if needed
- Create `.icns` icon from `.ico` if needed
- Build the macOS `.app` bundle
- Optionally create a `.dmg` installer

## Output

After successful build:
- **App Bundle**: `dist/SteamAchievementLocalizer.app`
- **DMG Installer** (optional): `dist/SteamAchievementLocalizer-v{version}-macOS.dmg`

## Manual Build

If you prefer to build manually:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install PyInstaller
pip install pyinstaller

# 3. Create .icns icon (if not exists)
mkdir -p assets/icon.iconset
sips -s format png assets/icon.ico --out assets/icon.iconset/icon_512x512.png -z 512 512
sips -s format png assets/icon.ico --out assets/icon.iconset/icon_256x256.png -z 256 256
sips -s format png assets/icon.ico --out assets/icon.iconset/icon_128x128.png -z 128 128
sips -s format png assets/icon.ico --out assets/icon.iconset/icon_32x32.png -z 32 32
sips -s format png assets/icon.ico --out assets/icon.iconset/icon_16x16.png -z 16 16
iconutil -c icns assets/icon.iconset -o assets/icon.icns
rm -rf assets/icon.iconset

# 4. Build the app
pyinstaller SteamAchievementLocalizer-macOS.spec --noconfirm

# 5. Test the app
open dist/SteamAchievementLocalizer.app
```

## Creating DMG Installer

```bash
# Create temporary directory
mkdir -p dist/dmg_temp
cp -R dist/SteamAchievementLocalizer.app dist/dmg_temp/
ln -s /Applications dist/dmg_temp/Applications

# Create DMG
hdiutil create -volname "Steam Achievement Localizer" \
    -srcfolder dist/dmg_temp \
    -ov -format UDZO \
    dist/SteamAchievementLocalizer-macOS.dmg

# Clean up
rm -rf dist/dmg_temp
```

## Testing

```bash
# Run the app
open dist/SteamAchievementLocalizer.app

# Or run from command line for debugging
dist/SteamAchievementLocalizer.app/Contents/MacOS/SteamAchievementLocalizer
```

## App Bundle Structure

```
SteamAchievementLocalizer.app/
├── Contents/
│   ├── Info.plist          # App metadata
│   ├── MacOS/
│   │   └── SteamAchievementLocalizer  # Executable
│   ├── Resources/
│   │   ├── icon.icns       # App icon
│   │   ├── assets/         # Application assets
│   │   └── plugins/        # Python plugins
│   └── Frameworks/         # PyQt6 and dependencies
```

## Troubleshooting

### Gatekeeper Warning

On first launch, macOS may show a warning because the app is not signed:
1. Right-click the app
2. Select "Open"
3. Click "Open" in the dialog

### App Won't Launch

Check the console output:
```bash
dist/SteamAchievementLocalizer.app/Contents/MacOS/SteamAchievementLocalizer
```

### Missing Dependencies

Make sure all Python dependencies are installed:
```bash
pip install -r requirements.txt
```

## GitHub Actions

The project includes automated macOS builds via GitHub Actions. On tag push:
1. Builds `.app` bundle
2. Creates `.dmg` installer
3. Uploads to GitHub Releases

See `.github/workflows/release-on-tag.yml` for details.

## Code Signing (Optional)

For distribution, you should sign the app with your Apple Developer certificate:

```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" \
    dist/SteamAchievementLocalizer.app

# Verify signature
codesign --verify --verbose dist/SteamAchievementLocalizer.app
spctl -a -v dist/SteamAchievementLocalizer.app
```

## Notarization (Optional)

For Gatekeeper approval:

```bash
# Create a zip for notarization
ditto -c -k --keepParent dist/SteamAchievementLocalizer.app SteamAchievementLocalizer.zip

# Submit for notarization
xcrun notarytool submit SteamAchievementLocalizer.zip \
    --apple-id "your@email.com" \
    --team-id "TEAM_ID" \
    --password "app-specific-password" \
    --wait

# Staple the notarization ticket
xcrun stapler staple dist/SteamAchievementLocalizer.app
```

Note: Code signing and notarization require an Apple Developer account.

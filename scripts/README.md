# Build and Maintenance Scripts

This directory contains utility scripts for building and maintaining the Steam Achievement Localizer project.

## Scripts

### `build_macos.sh`

Builds a macOS `.app` bundle and optionally creates a `.dmg` installer.

**Usage:**
```bash
./scripts/build_macos.sh
```

**What it does:**
1. Checks and activates virtual environment
2. Installs PyInstaller if needed
3. Creates `.icns` icon from `.ico` if needed
4. Builds the macOS app bundle using PyInstaller
5. Optionally creates a DMG installer

**Requirements:**
- macOS 10.13 or later
- Python 3.9+
- Virtual environment activated

**Output:**
- `dist/SteamAchievementLocalizer.app` - macOS application bundle
- `dist/SteamAchievementLocalizer-v{version}-macOS.dmg` - DMG installer (optional)

---

### `bump_version.py`

Updates version numbers across the project files.

**Usage:**
```bash
python scripts/bump_version.py --file SteamAchievementLocalizer.py --bump [major|minor|patch|none]
```

**Arguments:**
- `--file`: Path to the main Python file containing `APP_VERSION`
- `--bump`: Version bump type:
  - `major`: Increment major version (X.0.0)
  - `minor`: Increment minor version (0.X.0)
  - `patch`: Increment patch version (0.0.X)
  - `none`: Don't change version (useful for checking current version)

**What it updates:**
1. `APP_VERSION` in the main Python file
2. `version` in `SteamAchievementLocalizer-macOS.spec`
3. `CFBundleShortVersionString` in the spec file
4. `CFBundleVersion` in the spec file

**Example:**
```bash
# Bump patch version (0.8.3 -> 0.8.4)
python scripts/bump_version.py --file SteamAchievementLocalizer.py --bump patch

# Bump minor version (0.8.3 -> 0.9.0)
python scripts/bump_version.py --file SteamAchievementLocalizer.py --bump minor

# Bump major version (0.8.3 -> 1.0.0)
python scripts/bump_version.py --file SteamAchievementLocalizer.py --bump major

# Check current version without changing
python scripts/bump_version.py --file SteamAchievementLocalizer.py --bump none
```

**Output:**
- Prints the new version to stdout
- Prints update messages to stderr

---

## GitHub Actions Integration

These scripts are also used in the GitHub Actions workflows for automated builds and releases.

See `.github/workflows/` for more details.

---

## Development Workflow

### Local Development

1. Make your changes
2. Test locally:
   ```bash
   source .venv/bin/activate
   python SteamAchievementLocalizer.py
   ```

### Building for Distribution

1. Bump version:
   ```bash
   python scripts/bump_version.py --file SteamAchievementLocalizer.py --bump patch
   ```

2. Build for macOS:
   ```bash
   ./scripts/build_macos.sh
   ```

3. Test the built app:
   ```bash
   open dist/SteamAchievementLocalizer.app
   ```

### Creating a Release

1. Commit your changes
2. Tag the release:
   ```bash
   git tag v0.8.4
   git push origin v0.8.4
   ```

3. GitHub Actions will automatically:
   - Build for Windows (ZIP)
   - Build for Linux (AppImage)
   - Build for macOS (DMG)
   - Create a GitHub release with all artifacts

---

## Troubleshooting

### build_macos.sh fails

- Ensure virtual environment is activated
- Check that PyQt6 is installed: `pip install -r requirements.txt`
- Verify icon exists: `ls -la assets/icon.icns`

### bump_version.py doesn't update spec file

- Check that spec file exists: `SteamAchievementLocalizer-macOS.spec`
- Verify version format in spec file matches regex patterns

### DMG creation fails

- Ensure you have enough disk space
- Check that the app bundle was created successfully
- Try cleaning build artifacts: `rm -rf dist/ build/`

---

## Adding New Build Scripts

When adding new build scripts:

1. Make them executable: `chmod +x scripts/your_script.sh`
2. Add proper error handling
3. Update this README
4. Test on target platform
5. Consider GitHub Actions integration

# Changelog

All notable changes to Steam Achievement Localizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).




## [0.8.21] - 2025-12-28
### Added
- **Shortcuts**: Added keyboard shortcuts for saving: `Ctrl+S` (Save to Steam) and `Ctrl+Shift+S` (Save As / Manual Save).

## [0.8.20] - 2025-12-28
### Changed
- **Auto-Updater**: The application now explicitly asks for confirmation ("Yes" to restart and install, "No" to wait) after downloading an update.
- **Auto-Updater**: Now fetches and displays the full changelog history from GitHub for all missed versions instead of just the latest release notes.
- **UI**: Increased the update dialog size for better readability of release notes.
### Added
- **Localization**: Added English, Ukrainian, and Polish translations for the new update confirmation dialog.

## [0.8.19] - 2025-12-28

### Changed
- **Steam Logic**: Improved restart functionality to check if Steam is running before attempting to restart.
- **Localization**: Updated binary deletion confirmation dialog to explicitly show the game name.
- **Localization**: Refined error messages for rate limits and failed fetches to be more precise ("game names" instead of "games").

## [0.8.18] - 2025-12-27

### Added
- **Restart Steam**: Added functionality to restart the Steam client directly from the application via the File menu or Save confirmation dialog.
- **Localization**: Added translation keys for the new restart functionality in English, Ukrainian, and Polish.

### Fixed
- **AppImage**: Fixed "Open in Steam Store" button functionality on Linux AppImage builds by sanitizing the environment variables before launching the browser.

## [0.8.17] - 2025-12-25

### Fixed
- **Auto-Updater**: Fixed an issue where the auto-updater would not initialize or show update notifications on startup.
- **Icon Loader**: Fixed a bug where the icon loading progress bar would not disappear, and issues with loading icons and game names.
- **Localization**: Added Polish and Ukrainian translations for "games could not be fetched" and rate limit messages in `UserGameStatsListDialog`.
- **Safety**: Added fallback for `requests` import in `game_name_fetch_worker.py` and `user_game_stats_list_dialog.py` to prevent crashes on systems with missing dependencies.

## [0.8.16] - 2025-12-25

### Fixed
- **Performance**: Resolved an issue causing excessively long loading times for achievement icons.
- **Icons**: Optimized asynchronous icon loading to prevent UI delays.

## [0.8.15] - 2025-12-24

### Added
- **Icons**: Added achievement icon support with local caching and display in table.
- **Icons**: Added "Load achievement icons" toggle in File menu and startup dialog.
- **UI**: Added dynamic window title showing the currently loaded game name.
- **Game List**: Added "Open in Steam Store" and "Open in File Manager" buttons to game list dialog.

### Changed
- **UI**: Enhanced "Get Achievements" buttons visibility (bold, default action).
- **UI**: Implemented theme-aware zebra striping for achievement rows to improve readability.
- **UX**: Improved progress bar text formatting to eliminate duplicate counters.

### Fixed
- **Safety**: Binary file saving now prevents overwriting of `icon` and `icon_gray` columns, preserving original file hashes.
- **Performance**: Optimized icon loading to prioritize local cache and skip network requests when possible.

## [0.8.14] - 2025-12-24

### Added
- **Auto-Updater**: Added automatic update check on application startup

### Fixed
- **Auto-Updater**: Fixed AppImage path detection using `APPIMAGE` environment variable (was showing "Not running as AppImage" error)

## [0.8.13] - 2025-12-24

### Added
- **Game List Dialog**: Added "Open in Steam Store" button to open game's Steam Store page in browser
- **Game List Dialog**: Added "Open in File Manager" button to open achievements file folder
- **Translations**: Added new UI strings for Steam Store and File Manager buttons (English, Ukrainian, Polish)
- **Translations**: Added tooltips for new buttons in all supported languages

### Fixed
- **Linux Build**: Fixed `ModuleNotFoundError: No module named 'requests'` in Nuitka builds by adding `--include-package=requests` to build configuration
- **SSL Certificates**: Fixed SSL certificate verification errors in Linux builds by ensuring `certifi` package data is properly bundled
- **GitHub Actions**: Added `ca-certificates` to system dependencies for reliable SSL support in CI builds
- **Localization**: Fixed merge conflict errors in `lang_en.json` (incorrect "Pomoc" translation)
- **Localization**: Removed duplicate keys and tooltip entries in `lang_pl.json`

### Changed
- **Build System**: Updated local Linux build script (`build_linux_local.sh`) to use Python 3.12 explicitly
- **CI/CD**: Enhanced GitHub Actions workflow with certifi verification checks
- **Build System**: Added `.gitignore` entry for `SteamAchievementLocalizer.AppDir/` temporary build directory

## [0.8.12] - 2025-12-18

### Added
- Auto-updater plugin for automatic updates.

### Changed
- **Auto-updater**: Migrated from `urllib` to `requests` library for better SSL/HTTPS handling in AppImage and macOS builds.
- **Steam API**: Migrated Steam game name fetching from `urllib` to `requests` for improved reliability.
- Updated build workflow procedures in GitHub Actions.

### Fixed
- **Linux/macOS**: Fixed SSL certificate verification issues by using `requests` library which has superior certificate management.
- Import urllib.request for Nuitka and py2app builds.

## [0.8.11] - 2025-12-18

### Added
- Game name fetching worker for async Steam game name fetching (`game_name_fetch_worker.py`).
- Steam API all game names cache file (`steam.api.allgamenames.json`).
- Progress bar to status bar for visual feedback during long Steam API operations.
- Batch progress tracking for loading multiple games from Steam API.
- Progress helper methods: `show_progress()`, `update_progress()`, `hide_progress()`.
- `get_steam_game_name_without_progress()` method for batch operations.
- Progress dialog plugin to build configuration.

### Changed
- Updated Ukrainian, English, and Polish localization files.
- Updated binary parser, drag-drop overlay, and user stats dialog.
- Calculate total count before loading to show accurate progress (e.g., "Loading 1/101").
- Updated tooltips to warn about internet requirement for Steam API names.
- Updated setup.py and plugin initialization.

### Fixed
- Fixed infinite recursion in `load_json_with_fallback`.
- Fixed `force_manual_path` flag handling.

### Removed
- Removed `progress_dialog.py` (replaced with new implementation).

## [0.8.10] - 2025-12-17

### Fixed
- **Critical**: Fixed `gamename()` and `version()` functions re-reading files instead of using already loaded data, causing incorrect game information display when switching between manual and Steam ID file loading modes.
- Fixed Game ID field being overwritten when loading files manually. Game ID from manual files is now stored separately in `manual_file_game_id` variable.
- Fixed "Available Files" dialog not resetting `force_manual_path` flag on parent window, causing wrong file to be loaded after selecting game from dialog.
- Fixed "Get Achievements" button not resetting `force_manual_path` flag when loading by Game ID, potentially loading wrong file after manual file selection.

## [0.8.9] - 2025-12-16

### Changed
- Updated build workflow procedures in GitHub Actions.
- Refined build metadata and versioning configuration.
- Changed author name in LICENSE file to Latin characters for better compatibility.

### Fixed
- Fixed duplicate "unsaved changes" prompt appearing multiple times when loading files via drag-and-drop.

## [0.8.8] - 2025-12-16

### Fixed
- Fixed row height explosion on save when hidden columns are present.
- Fixed file manager not opening on Linux Nuitka builds by clearing `LD_LIBRARY_PATH`.
- Removed debug print from highlight delegate.

## [0.8.7] - 2025-12-12

### Changed
- Universalized column control and automated language mapping.
- Implemented dynamic mandatory column determination based on selected translation language.
- Automated `ui_to_steam_lang` mapping using available locales.
- Updated UI builder to respect dynamic mandatory columns.
- Changed storage logic to save `VisibleColumns` instead of `HiddenColumns`, with automatic migration.
- New columns in games are now automatically visible.
- Added "Select All" / "Deselect All" buttons to columns menu with translations (ua, en, pl).
- Tools menu is now macOS-only; Windows/Linux have stats action directly in menubar.
- Changed icon for find/replace action in context menu.

### Fixed
- Fixed formatting in `_create_about_action` method.
- Fixed row heights skipping hidden columns during calculation.

## [0.8.6] - 2025-12-09

### Changed
- Removed system language dependency; default fallback is now Ukrainian.
- Refactored CSV error handling for localization.
- Added and fixed Ukrainian translations.
- Prepared diagnostics for Linux file manager opening.

## [0.8.5] - 2025-12-09

### Fixed
- Fixed crash on save due to missing `context_lang_combo` attribute (now uses `translation_lang_combo` with fallback).

## [0.8.4] - 2025-12-08

### Added
- Full macOS support with native menu bar integration
- py2app build system for macOS application packaging
- ContextMenuManager plugin for unified context menus with icons

### Changed
- Updated about message with new contributors in Polish and Ukrainian localizations

## [0.8.3] - 2025-12-05

### Fixed
- Themes not working on Windows
- Windows build switched from Nuitka to PyInstaller for better compatibility
- ICU libraries bundling for Qt on Windows

## [0.8.2] - 2025-12-03

### Added
- Tooltips for all interactive UI elements
- Status bar showing application state and messages
- Help dialog with documentation
- Collapsible file search section for cleaner UI
- Steam game names database for auto-detection of games
- System accent color handling for theme highlights
- Accent color selection feature with localization support
- CHANGELOG.md for tracking version history

### Changed
- **Build System**: Switched from single executable (onefile) to ZIP archive for Windows
- **Build System**: Switched to AppImage for Linux distribution  
- **Build System**: Include all assets (themes, locales, game database) in builds
- Major UI improvements and plugin restructuring
- Enhanced user feedback system
- Improved search function
- License change

### Fixed
- Various bug fixes and stability improvements
- Plugin restructuring fixes

## [0.8.1]

### Added
- Collapsible file search section for cleaner UI
- Tooltips for all interactive elements
- Status bar showing application state
- Help dialog with documentation
- Plugin-based architecture improvements

### Changed
- Refactored UI components into separate plugins
- Improved file search functionality
- Enhanced user feedback system

## [0.8.0]

### Added
- Steam game names database for auto-detection
- Theme management system with multiple themes:
  - System (follows OS accent color)
  - Dark
  - Light  
  - Catppuccin Mocha
  - Femboy
  - Dark Femboy
- Accent color selection feature
- File manager plugin
- Steam integration plugin
- Language codes plugin
- UI builder plugin

### Changed
- Major plugin restructuring
- Translation controls now only show for English UI

## [0.7.8]

### Added
- Dynamic locale loading system
- Polish localization (lang_pl.json)
- Ukrainian localization (lang_ua.json)

### Changed
- Improved Steam language codes and mappings
- Better font application logic

## [0.7.7]

### Added
- Find and Replace dialog
- Context language dialog
- User game stats list dialog
- Highlight delegate for search results
- CSV handler plugin
- Binary parser plugin

### Changed
- Improved overall stability
- Better error handling

## [0.7.6]

### Added
- Initial public release
- Binary file parsing for Steam achievement files
- CSV import/export functionality
- Multi-language UI support
- Windows and Linux support

---

For older versions, see the [GitHub Releases](https://github.com/PanVena/SteamAchievementLocalizer/releases) page.

# Changelog

All notable changes to Steam Achievement Localizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).



## [0.8.12] - 2025-12-18

### Added
- Auto-updater plugin for automatic updates.

### Changed
- Updated build workflow procedures in GitHub Actions.

### Fixed
- **Linux/macOS**: Fixed SSL certificate verification issues in AppImage and .app builds by properly bundling certifi data files.
- Improved cross-platform SSL context creation with better error handling and fallback mechanisms for frozen builds.
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

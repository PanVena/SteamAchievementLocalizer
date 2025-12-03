# Changelog

All notable changes to Steam Achievement Localizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

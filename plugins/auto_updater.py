"""
Auto-updater plugin for Steam Achievement Localizer
Checks for updates from GitHub releases and handles cross-platform installation
"""

import sys
import os
import json
import time
import tempfile
import shutil
import subprocess
import zipfile
import ssl
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple


def create_ssl_context():
    """Create SSL context that works cross-platform (macOS, Linux, Windows)"""
    # Try certifi first
    try:
        import certifi
        cert_path = certifi.where()
        # Verify the cert file actually exists (important for AppImage/frozen builds)
        if os.path.isfile(cert_path):
            return ssl.create_default_context(cafile=cert_path)
    except (ImportError, FileNotFoundError, OSError):
        pass
    
    # Fallback to system certificates
    try:
        return ssl.create_default_context()
    except Exception:
        # Last resort: unverified context (less secure but works)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

from PyQt6.QtCore import QThread, pyqtSignal, QSettings, Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QMessageBox, QCheckBox
)
from PyQt6.QtGui import QFont


GITHUB_REPO = "PanVena/SteamAchievementLocalizer"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CHECK_INTERVAL_HOURS = 4


def compare_versions(current: str, latest: str) -> int:
    """
    Compare two version strings (semver format).
    Returns: -1 if current < latest, 0 if equal, 1 if current > latest
    """
    def parse_version(v: str) -> Tuple[int, ...]:
        v = v.lstrip('v')
        parts = v.split('.')
        return tuple(int(p) for p in parts if p.isdigit())

    current_parts = parse_version(current)
    latest_parts = parse_version(latest)

    for i in range(max(len(current_parts), len(latest_parts))):
        c = current_parts[i] if i < len(current_parts) else 0
        l = latest_parts[i] if i < len(latest_parts) else 0
        if c < l:
            return -1
        elif c > l:
            return 1
    return 0


class UpdateChecker(QThread):
    """Thread for checking updates from GitHub"""
    update_available = pyqtSignal(dict)  # Emits release info if update available
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, current_version: str, force_check: bool = False):
        super().__init__()
        self.current_version = current_version
        self.force_check = force_check
        self.settings = QSettings("Vena", "Steam Achievement Localizer")

    def should_check(self) -> bool:
        """Check if enough time has passed since last check"""
        if self.force_check:
            return True

        last_check = self.settings.value("last_update_check", 0, type=int)
        current_time = int(time.time())
        hours_passed = (current_time - last_check) / 3600

        return hours_passed >= CHECK_INTERVAL_HOURS

    def run(self):
        if not self.should_check():
            self.no_update.emit()
            return

        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    'User-Agent': 'SteamAchievementLocalizer',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )

            ssl_context = create_ssl_context()
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))

            # Update last check time
            self.settings.setValue("last_update_check", int(time.time()))
            self.settings.sync()

            latest_version = data.get('tag_name', '').lstrip('v')

            # Check if user skipped this version
            skipped_version = self.settings.value("skipped_version", "")
            if skipped_version == latest_version and not self.force_check:
                self.no_update.emit()
                return

            if compare_versions(self.current_version, latest_version) < 0:
                # Prepare release info
                release_info = {
                    'version': latest_version,
                    'tag_name': data.get('tag_name', ''),
                    'body': data.get('body', ''),
                    'html_url': data.get('html_url', ''),
                    'assets': []
                }

                for asset in data.get('assets', []):
                    release_info['assets'].append({
                        'name': asset.get('name', ''),
                        'size': asset.get('size', 0),
                        'download_url': asset.get('browser_download_url', '')
                    })

                self.update_available.emit(release_info)
            else:
                self.no_update.emit()

        except urllib.error.HTTPError as e:
            self.error_occurred.emit(f"HTTP Error: {e.code}")
        except urllib.error.URLError as e:
            self.error_occurred.emit(f"Network Error: {str(e.reason)}")
        except Exception as e:
            self.error_occurred.emit(str(e))


class UpdateDownloader(QThread):
    """Thread for downloading update files"""
    progress = pyqtSignal(int, int)  # bytes_downloaded, total_bytes
    download_complete = pyqtSignal(str)  # path to downloaded file
    error_occurred = pyqtSignal(str)

    def __init__(self, download_url: str, filename: str):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            temp_dir = tempfile.mkdtemp(prefix="sal_update_")
            file_path = os.path.join(temp_dir, self.filename)

            req = urllib.request.Request(
                self.download_url,
                headers={'User-Agent': 'SteamAchievementLocalizer'}
            )

            ssl_context = create_ssl_context()
            with urllib.request.urlopen(req, timeout=60, context=ssl_context) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(file_path, 'wb') as f:
                    while True:
                        if self.cancelled:
                            f.close()
                            os.remove(file_path)
                            return

                        chunk = response.read(8192)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)

            self.download_complete.emit(file_path)

        except Exception as e:
            self.error_occurred.emit(str(e))


class UpdateInstaller:
    """Handles platform-specific update installation"""

    @staticmethod
    def get_platform_asset_name() -> str:
        """Get the asset filename for current platform"""
        if sys.platform == "darwin":
            return "SteamAchievementLocalizer-macOS.dmg"
        elif sys.platform == "win32":
            return "SteamAchievementLocalizer-win64.zip"
        else:  # Linux
            return "SteamAchievementLocalizer-linux64.AppImage"

    @staticmethod
    def get_download_url(assets: list) -> Optional[str]:
        """Find download URL for current platform"""
        target_name = UpdateInstaller.get_platform_asset_name()
        for asset in assets:
            if asset['name'] == target_name:
                return asset['download_url']
        return None

    @staticmethod
    def get_current_app_path() -> str:
        """Get the path to the current application"""
        if sys.platform == "darwin":
            # For macOS .app bundle
            if getattr(sys, 'frozen', False):
                # Running as compiled app
                app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))))
                if app_path.endswith('.app'):
                    return app_path
            return sys.executable
        elif sys.platform == "win32":
            if getattr(sys, 'frozen', False):
                return os.path.dirname(sys.executable)
            return os.path.dirname(os.path.abspath(__file__))
        else:  # Linux
            if getattr(sys, 'frozen', False):
                return sys.executable
            return sys.executable

    @staticmethod
    def install_macos(dmg_path: str) -> Tuple[bool, str]:
        """Install update on macOS from DMG"""
        try:
            # Get current app path
            current_app = UpdateInstaller.get_current_app_path()
            if not current_app.endswith('.app'):
                return False, "Cannot determine current app location"

            app_dir = os.path.dirname(current_app)
            app_name = os.path.basename(current_app)

            # Mount DMG
            mount_result = subprocess.run(
                ['hdiutil', 'attach', '-nobrowse', '-quiet', dmg_path],
                capture_output=True, text=True
            )

            if mount_result.returncode != 0:
                return False, f"Failed to mount DMG: {mount_result.stderr}"

            # Find mounted volume
            mount_point = None
            for line in mount_result.stdout.strip().split('\n'):
                parts = line.split('\t')
                if len(parts) >= 3 and '/Volumes/' in parts[-1]:
                    mount_point = parts[-1].strip()
                    break

            if not mount_point:
                return False, "Could not find mounted volume"

            # Find .app in mounted volume
            new_app_path = None
            for item in os.listdir(mount_point):
                if item.endswith('.app'):
                    new_app_path = os.path.join(mount_point, item)
                    break

            if not new_app_path:
                subprocess.run(['hdiutil', 'detach', mount_point, '-quiet'])
                return False, "Could not find app in DMG"

            # Create update script that runs after app exits
            script_path = os.path.join(tempfile.gettempdir(), 'sal_update.sh')
            with open(script_path, 'w') as f:
                f.write(f'''#!/bin/bash
sleep 2
rm -rf "{current_app}"
cp -R "{new_app_path}" "{app_dir}/"
hdiutil detach "{mount_point}" -quiet
open "{os.path.join(app_dir, os.path.basename(new_app_path))}"
rm -f "{script_path}"
''')

            os.chmod(script_path, 0o755)
            subprocess.Popen(['/bin/bash', script_path], start_new_session=True)

            return True, "Update will be installed. Application will restart."

        except Exception as e:
            return False, str(e)

    @staticmethod
    def install_windows(zip_path: str) -> Tuple[bool, str]:
        """Install update on Windows from ZIP"""
        try:
            current_app = UpdateInstaller.get_current_app_path()

            # Extract to temp directory
            temp_extract = tempfile.mkdtemp(prefix="sal_update_extract_")

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_extract)

            # Find the extracted content (might be in a subdirectory)
            extracted_content = temp_extract
            items = os.listdir(temp_extract)
            if len(items) == 1 and os.path.isdir(os.path.join(temp_extract, items[0])):
                extracted_content = os.path.join(temp_extract, items[0])

            # Create batch script for update
            batch_path = os.path.join(tempfile.gettempdir(), 'sal_update.bat')
            exe_name = "SteamAchievementLocalizer.exe"

            with open(batch_path, 'w') as f:
                f.write(f'''@echo off
timeout /t 2 /nobreak > nul
xcopy /E /Y /Q "{extracted_content}\\*" "{current_app}\\"
rmdir /S /Q "{temp_extract}"
start "" "{os.path.join(current_app, exe_name)}"
del "%~f0"
''')

            subprocess.Popen(['cmd', '/c', batch_path],
                           creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                           start_new_session=True)

            return True, "Update will be installed. Application will restart."

        except Exception as e:
            return False, str(e)

    @staticmethod
    def install_linux(appimage_path: str) -> Tuple[bool, str]:
        """Install update on Linux (AppImage)"""
        try:
            current_app = UpdateInstaller.get_current_app_path()

            if not current_app.endswith('.AppImage'):
                return False, "Not running as AppImage, manual update required"

            # Create update script
            script_path = os.path.join(tempfile.gettempdir(), 'sal_update.sh')

            with open(script_path, 'w') as f:
                f.write(f'''#!/bin/bash
sleep 2
cp "{appimage_path}" "{current_app}"
chmod +x "{current_app}"
"{current_app}" &
rm -f "{script_path}"
rm -rf "$(dirname "{appimage_path}")"
''')

            os.chmod(script_path, 0o755)
            subprocess.Popen(['/bin/bash', script_path], start_new_session=True)

            return True, "Update will be installed. Application will restart."

        except Exception as e:
            return False, str(e)

    @staticmethod
    def install(file_path: str) -> Tuple[bool, str]:
        """Install update based on current platform"""
        if sys.platform == "darwin":
            return UpdateInstaller.install_macos(file_path)
        elif sys.platform == "win32":
            return UpdateInstaller.install_windows(file_path)
        else:
            return UpdateInstaller.install_linux(file_path)


class UpdateDialog(QDialog):
    """Dialog showing update information and progress"""

    def __init__(self, release_info: dict, translations: dict, current_version: str, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.translations = translations
        self.current_version = current_version
        self.downloader = None
        self.settings = QSettings("Vena", "Steam Achievement Localizer")

        self.setup_ui()

    def get_text(self, key: str, default: str = "") -> str:
        """Get translated text"""
        return self.translations.get(key, default)

    def setup_ui(self):
        self.setWindowTitle(self.get_text("update_available", "Update Available"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header_label = QLabel(self.get_text("update_new_version_available", "A new version is available!"))
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Version info
        version_layout = QHBoxLayout()

        current_label = QLabel(f"{self.get_text('update_current_version', 'Current version')}: {self.current_version}")
        version_layout.addWidget(current_label)

        version_layout.addStretch()

        new_label = QLabel(f"{self.get_text('update_new_version', 'New version')}: {self.release_info['version']}")
        new_font = QFont()
        new_font.setBold(True)
        new_label.setFont(new_font)
        version_layout.addWidget(new_label)

        layout.addLayout(version_layout)

        # Release notes
        notes_label = QLabel(self.get_text("update_whats_new", "What's new:"))
        layout.addWidget(notes_label)

        notes_edit = QTextEdit()
        notes_edit.setReadOnly(True)
        notes_edit.setPlainText(self.release_info.get('body', 'No release notes available.'))
        notes_edit.setMaximumHeight(150)
        layout.addWidget(notes_edit)

        # Progress section (hidden initially)
        self.progress_label = QLabel("")
        self.progress_label.hide()
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Auto-update checkbox
        self.auto_check = QCheckBox(self.get_text("update_check_automatically", "Check for updates automatically"))
        self.auto_check.setChecked(self.settings.value("auto_update_enabled", True, type=bool))
        self.auto_check.toggled.connect(self.on_auto_check_changed)
        layout.addWidget(self.auto_check)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.skip_btn = QPushButton(self.get_text("update_skip_version", "Skip This Version"))
        self.skip_btn.clicked.connect(self.on_skip)
        button_layout.addWidget(self.skip_btn)

        self.later_btn = QPushButton(self.get_text("update_remind_later", "Remind Me Later"))
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)

        self.update_btn = QPushButton(self.get_text("update_now", "Update Now"))
        self.update_btn.setDefault(True)
        self.update_btn.clicked.connect(self.on_update)
        button_layout.addWidget(self.update_btn)

        layout.addLayout(button_layout)

    def on_auto_check_changed(self, checked: bool):
        self.settings.setValue("auto_update_enabled", checked)
        self.settings.sync()

    def on_skip(self):
        self.settings.setValue("skipped_version", self.release_info['version'])
        self.settings.sync()
        self.reject()

    def on_update(self):
        # Get download URL for current platform
        download_url = UpdateInstaller.get_download_url(self.release_info['assets'])

        if not download_url:
            QMessageBox.warning(
                self,
                self.get_text("error", "Error"),
                self.get_text("update_no_download", "No download available for your platform.")
            )
            return

        # Disable buttons and show progress
        self.update_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.later_btn.setText(self.get_text("cancel", "Cancel"))
        self.later_btn.clicked.disconnect()
        self.later_btn.clicked.connect(self.on_cancel_download)

        self.progress_label.setText(self.get_text("update_downloading", "Downloading update..."))
        self.progress_label.show()
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        # Start download
        filename = UpdateInstaller.get_platform_asset_name()
        self.downloader = UpdateDownloader(download_url, filename)
        self.downloader.progress.connect(self.on_download_progress)
        self.downloader.download_complete.connect(self.on_download_complete)
        self.downloader.error_occurred.connect(self.on_download_error)
        self.downloader.start()

    def on_cancel_download(self):
        if self.downloader:
            self.downloader.cancel()
        self.reject()

    def on_download_progress(self, downloaded: int, total: int):
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar.setValue(percent)

            # Show MB downloaded
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.progress_label.setText(
                f"{self.get_text('update_downloading', 'Downloading...')} {mb_downloaded:.1f} / {mb_total:.1f} MB"
            )

    def on_download_complete(self, file_path: str):
        self.progress_label.setText(self.get_text("update_installing", "Installing update..."))
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Install update
        success, message = UpdateInstaller.install(file_path)

        if success:
            QMessageBox.information(
                self,
                self.get_text("update_success", "Update"),
                self.get_text("update_restart_message", "The application will now restart to complete the update.")
            )
            # Exit the application
            if self.parent():
                self.parent().close()
            sys.exit(0)
        else:
            QMessageBox.critical(
                self,
                self.get_text("error", "Error"),
                f"{self.get_text('update_install_failed', 'Failed to install update')}: {message}"
            )
            self.reset_ui()

    def on_download_error(self, error: str):
        QMessageBox.critical(
            self,
            self.get_text("error", "Error"),
            f"{self.get_text('update_download_failed', 'Failed to download update')}: {error}"
        )
        self.reset_ui()

    def reset_ui(self):
        self.progress_label.hide()
        self.progress_bar.hide()
        self.update_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.later_btn.setText(self.get_text("update_remind_later", "Remind Me Later"))
        self.later_btn.clicked.disconnect()
        self.later_btn.clicked.connect(self.reject)


class AutoUpdater:
    """Main auto-updater class for use in the application"""

    def __init__(self, current_version: str, translations: dict, parent=None):
        self.current_version = current_version
        self.translations = translations
        self.parent = parent
        self.checker = None
        self.settings = QSettings("Vena", "Steam Achievement Localizer")

    def check_for_updates(self, manual: bool = False, callback=None):
        """
        Check for updates.
        manual: If True, always check and show dialog even if no update
        callback: Optional callback function(has_update: bool)
        """
        # Check if auto-update is enabled (for automatic checks)
        if not manual and not self.settings.value("auto_update_enabled", True, type=bool):
            if callback:
                callback(False)
            return

        self.checker = UpdateChecker(self.current_version, force_check=manual)
        self.manual_check = manual
        self.callback = callback

        self.checker.update_available.connect(self._on_update_available)
        self.checker.no_update.connect(self._on_no_update)
        self.checker.error_occurred.connect(self._on_error)
        self.checker.start()

    def _on_update_available(self, release_info: dict):
        if self.callback:
            self.callback(True)

        dialog = UpdateDialog(release_info, self.translations, self.current_version, self.parent)
        dialog.exec()

    def _on_no_update(self):
        if self.callback:
            self.callback(False)

        if self.manual_check:
            QMessageBox.information(
                self.parent,
                self.translations.get("update_check", "Update Check"),
                self.translations.get("update_up_to_date", "You are using the latest version.")
            )

    def _on_error(self, error: str):
        if self.callback:
            self.callback(False)

        if self.manual_check:
            QMessageBox.warning(
                self.parent,
                self.translations.get("error", "Error"),
                f"{self.translations.get('update_check_failed', 'Failed to check for updates')}: {error}"
            )

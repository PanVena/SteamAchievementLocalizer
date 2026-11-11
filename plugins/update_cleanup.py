"""One-time cleanup for stale data and Linux desktop associations."""

import os
import stat
import sys
import tempfile

from PyQt6.QtCore import QSettings

from plugins.icon_loader import IconLoader


_APP_ID_FRAGMENT = "steamachievementlocalizer"
_OCTET_STREAM = "application/octet-stream"
_CACHE_MIGRATION_KEY = "Migrations/clear_app_caches_v1"
_MIME_MIGRATION_KEY = "Migrations/remove_legacy_mime_v1"


def _rewrite_semicolon_list(line, should_remove):
    line_ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
    content = line[:-len(line_ending)] if line_ending else line
    key, separator, value = content.partition("=")
    if not separator:
        return line, False

    values = [item.strip() for item in value.split(";") if item.strip()]
    kept = [item for item in values if not should_remove(item)]
    removed = len(kept) != len(values)
    if not removed:
        return line, False
    if not kept:
        return None, True

    trailing_separator = ";" if value.rstrip().endswith(";") else ""
    return f"{key}={';'.join(kept)}{trailing_separator}{line_ending}", True


def _write_lines_atomically(path, lines):
    temporary_path = None
    try:
        mode = stat.S_IMODE(os.stat(path).st_mode)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", dir=os.path.dirname(path), delete=False
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.writelines(lines)
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    except OSError as error:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError as cleanup_error:
                raise OSError(
                    f"{error}; temporary file cleanup failed: {cleanup_error}"
                ) from error
        raise


def _rewrite_ini_list(path, sections, key, should_remove):
    if not os.path.isfile(path) or os.path.islink(path):
        return False

    with open(path, "r", encoding="utf-8", newline="") as source:
        lines = source.readlines()

    current_section = None
    rewritten = []
    changed = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped[1:-1]
        if current_section in sections and line.partition("=")[0].strip() == key:
            updated_line, line_changed = _rewrite_semicolon_list(line, should_remove)
            if line_changed:
                changed = True
                if updated_line is not None:
                    rewritten.append(updated_line)
                continue
        rewritten.append(line)

    if changed:
        _write_lines_atomically(path, rewritten)
    return changed


def _rewrite_desktop_file(path):
    with open(path, "r", encoding="utf-8", newline="") as source:
        lines = source.readlines()

    rewritten = []
    changed = False
    for line in lines:
        if line.partition("=")[0].strip() == "MimeType":
            updated_line, line_changed = _rewrite_semicolon_list(
                line, lambda mime_type: mime_type.strip() == _OCTET_STREAM
            )
            if line_changed:
                changed = True
                if updated_line is not None:
                    rewritten.append(updated_line)
                continue
        rewritten.append(line)

    if changed:
        _write_lines_atomically(path, rewritten)
    return changed


def cleanup_legacy_linux_associations(config_home=None, data_home=None):
    """Remove only this app's old catch-all MIME registration from user data."""
    if sys.platform != "linux":
        return []

    home = os.path.expanduser("~")
    config_home = config_home or os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    data_home = data_home or os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    applications_dir = os.path.join(data_home, "applications")
    errors = []

    try:
        with os.scandir(applications_dir) as entries:
            for entry in entries:
                if (
                    not entry.name.lower().endswith(".desktop")
                    or _APP_ID_FRAGMENT not in entry.name.lower()
                    or not entry.is_file(follow_symlinks=False)
                ):
                    continue
                try:
                    _rewrite_desktop_file(entry.path)
                except (OSError, UnicodeError) as error:
                    errors.append(f"{entry.path}: {error}")
    except FileNotFoundError:
        pass
    except OSError as error:
        errors.append(f"{applications_dir}: {error}")

    mimeapps_paths = {
        os.path.join(config_home, "mimeapps.list"),
        os.path.join(applications_dir, "mimeapps.list"),
        os.path.join(applications_dir, "defaults.list"),
    }
    try:
        mimeapps_paths.update(
            os.path.join(config_home, name)
            for name in os.listdir(config_home)
            if name.endswith("-mimeapps.list")
        )
    except FileNotFoundError:
        pass
    except OSError as error:
        errors.append(f"{config_home}: {error}")

    for path in mimeapps_paths:
        try:
            _rewrite_ini_list(
                path,
                {"Default Applications", "Added Associations"},
                _OCTET_STREAM,
                lambda app_id: _APP_ID_FRAGMENT in app_id.lower(),
            )
        except (OSError, UnicodeError) as error:
            errors.append(f"{path}: {error}")

    try:
        _rewrite_ini_list(
            os.path.join(applications_dir, "mimeinfo.cache"),
            {"MIME Cache"},
            _OCTET_STREAM,
            lambda app_id: _APP_ID_FRAGMENT in app_id.lower(),
        )
    except (OSError, UnicodeError) as error:
        errors.append(f"{applications_dir}/mimeinfo.cache: {error}")

    return errors


def run_post_update_cleanup(settings):
    """Clean app-owned stale state once, preserving unrelated user settings."""
    errors = []

    if not settings.value(_CACHE_MIGRATION_KEY, False, type=bool):
        try:
            settings.remove("GameNameCache")
            IconLoader(settings).clear_cache()
            settings.setValue(_CACHE_MIGRATION_KEY, True)
            settings.sync()
            if settings.status() != QSettings.Status.NoError:
                errors.append("Could not save the app-cache cleanup marker.")
        except OSError as error:
            errors.append(f"Could not clear app caches: {error}")

    if not settings.value(_MIME_MIGRATION_KEY, False, type=bool):
        mime_errors = cleanup_legacy_linux_associations()
        errors.extend(mime_errors)
        if not mime_errors:
            settings.setValue(_MIME_MIGRATION_KEY, True)
            settings.sync()
            if settings.status() != QSettings.Status.NoError:
                errors.append("Could not save the MIME cleanup marker.")

    return errors

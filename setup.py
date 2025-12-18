"""
py2app setup script for Steam Achievement Localizer
"""

from setuptools import setup
import os

# Get version from source
VERSION = "0.8.12"
with open("SteamAchievementLocalizer.py", "r", encoding="utf-8") as f:
    for line in f:
        if "APP_VERSION" in line:
            VERSION = line.split('"')[1]
            break

APP = ['SteamAchievementLocalizer.py']
DATA_FILES = [
    ('assets', ['assets/icon.icns']),
    ('assets/locales', [
        'assets/locales/lang_en.json',
        'assets/locales/lang_pl.json',
        'assets/locales/lang_ua.json',
    ]),
    ('assets/themes', [
        'assets/themes/catppuccin_mocha.json',
        'assets/themes/dark.json',
        'assets/themes/darkfemboy.json',
        'assets/themes/femboy.json',
        'assets/themes/light.json',
        'assets/themes/system.json',
        'assets/steam.api.allgamenames.json',
    ]),
]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/icon.icns',
    'plist': {
        'CFBundleName': 'Steam Achievement Localizer',
        'CFBundleDisplayName': 'Steam Achievement Localizer',
        'CFBundleIdentifier': 'com.panvena.steamachievementlocalizer',
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'CFBundleGetInfoString': f'Steam Achievement Localizer {VERSION}, Copyright © 2025 Pan Vena',
        'NSHumanReadableCopyright': 'Copyright © 2025 Pan Vena. MIT License.',
        'NSHumanReadableDescription': 'Tool for localizing Steam achievement files',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Steam Achievement Schema',
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['public.data'],
                'LSHandlerRank': 'Owner',
            }
        ],
    },
    'packages': ['PyQt6'],
    'includes': [
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'certifi',
        'plugins.highlight_delegate',
        'plugins.find_replace_dialog',
        'plugins.user_game_stats_list_dialog',
        'plugins.context_lang_dialog',
        'plugins.theme_manager',
        'plugins.binary_parser',
        'plugins.steam_integration',
        'plugins.csv_handler',
        'plugins.file_manager',
        'plugins.ui_builder',
        'plugins.help_dialog',
        'plugins.context_menu',
        'plugins.steam_lang_codes',
        'plugins.drag_drop_overlay',
        'plugins.game_name_fetch_worker',
        'plugins.auto_updater',
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
    ],
}

setup(
    name='Steam Achievement Localizer',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    version=VERSION,
    description='Tool for localizing Steam achievement files',
    author='Pan Vena',
    url='https://github.com/PanVena/SteamAchievementLocalizer',
)

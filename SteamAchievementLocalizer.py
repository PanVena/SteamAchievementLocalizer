import sys
import csv
import re
import os
import subprocess
import json
import shutil
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QIcon, QAction,QKeySequence, QTextDocument, QColor, QFontMetrics
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QHBoxLayout,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QFrame, QGroupBox, QHeaderView,
    QInputDialog, QMainWindow, QColorDialog, QAbstractItemView, QAbstractItemDelegate, QCheckBox
)
from plugins.highlight_delegate import HighlightDelegate
from plugins.find_replace_dialog import FindReplacePanel
from plugins.user_game_stats_list_dialog import UserGameStatsListDialog
from plugins.context_lang_dialog import ContextLangDialog
from plugins.theme_manager import ThemeManager
from plugins.binary_parser import BinaryParser
from plugins.steam_integration import SteamIntegration
from plugins.csv_handler import CSVHandler
from plugins.file_manager import FileManager
from plugins.ui_builder import UIBuilder
from plugins.steam_lang_codes import (
    get_available_languages_for_selection,
    get_display_name,
    get_system_language,
    get_code_from_display_name
)

if sys.platform == "win32":
    import winreg

APP_VERSION = "0.8.1" 

LOCALES_DIR = "assets/locales"

def load_available_locales():
    """Load available locales from the locales directory"""
    locales = {}
    if os.path.exists(LOCALES_DIR):
        for filename in os.listdir(LOCALES_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(LOCALES_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        locale_data = json.load(f)
                        # Check if locale has metadata
                        if '_locale_info' in locale_data:
                            locale_info = locale_data['_locale_info']
                            locale_name = locale_info.get('name')
                            if locale_name:
                                locales[locale_name] = {
                                    'file_path': file_path,
                                    'native_name': locale_info.get('native_name', locale_name),
                                    'code': locale_info.get('code', filename[5:7]),  # Extract from filename
                                    'priority': locale_info.get('priority', 999),
                                    'data': locale_data
                                }
                        else:
                            # Fallback for locales without metadata - use filename
                            if filename.startswith('lang_') and len(filename) >= 12:
                                code = filename[5:7]  # Extract code like "en" from "lang_en.json"
                                locale_name = f"Language_{code}".capitalize()
                                locales[locale_name] = {
                                    'file_path': file_path,
                                    'native_name': locale_name,
                                    'code': code,
                                    'priority': 999,
                                    'data': locale_data
                                }
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Error loading locale from {filename}: {e}")
    return locales

def get_sorted_locale_names(locales):
    """Get locale names sorted by priority and name"""
    locale_list = []
    for name, info in locales.items():
        priority = info.get('priority', 999)
        locale_list.append((priority, name))
    
    # Sort by priority (ascending), then by name (alphabetically)
    locale_list.sort(key=lambda x: (x[0], x[1]))
    return [name for priority, name in locale_list]

# Legacy support - will be replaced by automatic loading
LANG_FILES = {
    "English": "assets/locales/lang_en.json",
    "Українська": "assets/locales/lang_ua.json",
    "Polski": "assets/locales/lang_pl.json"
}


def choose_language():
    settings = QSettings("Vena", "Steam Achievement Localizer")
    current_language = settings.value("language", None)

    if current_language:
        return current_language  # Already saved language

    # Load available locales dynamically
    locales = load_available_locales()
    
    if not locales:
        return "English"  # Fallback if no locales found
    
    # Create language options from loaded locales
    lang_options = {}
    for locale_name, locale_info in locales.items():
        lang_options[locale_name] = locale_info['native_name']
    
    # Sort language options by priority
    sorted_names = get_sorted_locale_names(locales)
    sorted_options = [(name, lang_options[name]) for name in sorted_names if name in lang_options]
    
    lang, ok = QInputDialog.getItem(
        None,
        "Select Language",
        "Choose your language:",
        [display_name for name, display_name in sorted_options],
        0,
        False
    )
    
    if ok and lang:
        # Find the key for selected display name
        selected_key = None
        for name, display_name in sorted_options:
            if display_name == lang:
                selected_key = name
                break
        
        if selected_key:
            settings.setValue("language", selected_key)
            settings.sync()
            return selected_key

    # Default to first available locale or English
    default_locale = sorted_names[0] if sorted_names else "English"
    return default_locale

def resource_path(relative_path: str) -> str:
    """Returns the correct path to resources for both .py and .exe (Nuitka/PyInstaller)"""
    if getattr(sys, 'frozen', False):
        # When running as a bundled exe
        base_path = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(sys.executable)
    else:
        # When running as a normal .py file
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

def load_json_with_fallback(path):
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return json.load(f)
        except Exception:
            continue

    settings = QSettings("Vena", "Steam Achievement Localizer")
    language = settings.value("language", "English")
    translations = load_translations_for_language(language)
    raise RuntimeError(f"{translations.get('cannot_decode_json', 'Cannot decode JSON: ')}{path}")

def load_translations_for_language(language):
    """Load translations for a specific language using the new locale system"""
    locales = load_available_locales()
    
    # Try to find the requested language
    if language in locales:
        locale_info = locales[language]
        return locale_info['data']
    
    # Fallback to legacy system if not found in new system
    if language in LANG_FILES:
        return load_json_with_fallback(resource_path(LANG_FILES[language]))
    
    # Final fallback to English
    if "English" in locales:
        return locales["English"]['data']
    elif "English" in LANG_FILES:
        return load_json_with_fallback(resource_path(LANG_FILES["English"]))
    
    # Return empty dict if nothing works
    return {}
    
class BinParserGUI(QMainWindow):

    # =================================================================
    # INITIALIZATION AND UI SETUP
    # =================================================================
    
    def __init__(self, language="English"):
        self.modified = False
        super().__init__(parent=None)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.language = language
        
        # Initialize plugins first
        self.binary_parser = BinaryParser()
        self.steam_integration = SteamIntegration()
        self.csv_handler = CSVHandler()
        self.file_manager = FileManager()
        
        # Load Steam game names database
        self.steam_game_names = self.load_steam_game_names()
        
        # Load available locales and store for ui_builder access
        self.available_locales = load_available_locales()
        # Keep legacy LANG_FILES for backward compatibility
        self.LANG_FILES = LANG_FILES
        
        self.translations = self.load_language(language)
        self.setWindowTitle(f"{self.translations.get('app_title')}{APP_VERSION}")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.setMinimumSize(800, 400)
        self.set_window_size()

        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
        

        self.settings = QSettings("Vena", "Steam Achievement Localizer")
        self.default_steam_path = self.detect_steam_path()
        
        self.force_manual_path = False  


        # Create collapsible section for file search inputs
        self.file_search_section = QGroupBox()
        self.file_search_section.setCheckable(True)
        self.file_search_section.setChecked(True)  # Initially expanded
        self.file_search_section.setTitle(self.translations.get("file_search_section", "▼ File Search"))
        self.file_search_section.toggled.connect(self.on_file_search_section_toggled)
        self.file_search_section.setFlat(False)
        
        file_search_layout = QVBoxLayout()
        
        # --- File localization selection ---
        stats_bin_path_layout = QHBoxLayout()
        self.stats_bin_path_path = QLineEdit()
        self.stats_bin_path_path.setPlaceholderText(self.translations.get("man_select_file_label"))
        self.stats_bin_path_path.textChanged.connect(lambda text: self.settings.setValue("LastEnteredFilePath", text))
        self.stats_bin_path_btn = QPushButton(self.translations.get("man_select_file"))
        self.stats_bin_path_btn.clicked.connect(self.stats_bin_path_search)
        self.select_stats_bin_path_btn = QPushButton(self.translations.get("get_ach"))
        self.select_stats_bin_path_btn.clicked.connect(self.select_stats_bin_path)
        stats_bin_path_layout.addWidget(self.stats_bin_path_path)
        stats_bin_path_layout.addWidget(self.stats_bin_path_btn)
        stats_bin_path_layout.addWidget(self.select_stats_bin_path_btn)
        
        # --- Frame ---
        self.stats_group = QGroupBox(self.translations.get("man_file_sel_label"))
        self.stats_group.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.stats_group.setLayout(stats_bin_path_layout)
        file_search_layout.addWidget(self.stats_group)   
        
        
        # --- OR (with lines) ---
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Plain)
        line1.setStyleSheet("color: white; background-color: white;")

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Plain)
        line2.setStyleSheet("color: white; background-color: white;")

        self.abo_label = QLabel(self.translations.get("OR"))
        self.abo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.abo_label.setStyleSheet("color: white; font-weight: bold;")

        abo_layout = QHBoxLayout()
        abo_layout.addWidget(line1)
        abo_layout.addWidget(self.abo_label)
        abo_layout.addWidget(line2)

        
       # --- Frame ---
        box_1 = QGroupBox("")  
        box_1.setFlat(False)   
        box_1.setLayout(abo_layout)
        file_search_layout.addWidget(box_1)


        # --- Steam folder selection ---
        steam_folder_layout = QHBoxLayout()
        self.steam_folder_path = QLineEdit()
        self.steam_folder_path.setPlaceholderText(self.translations.get("steam_folder_label"))
        self.steam_folder_path.textChanged.connect(self.on_steam_path_changed)
        self.steam_auto_path_btn = QPushButton(self.translations.get("auto"))
        self.steam_auto_path_btn.clicked.connect(self.steam_auto_forcing)
        self.select_steam_folder_btn = QPushButton(self.translations.get("select_steam_folder"))
        self.select_steam_folder_btn.clicked.connect(self.select_steam_folder)
        steam_folder_layout.addWidget(self.steam_folder_path)
        steam_folder_layout.addWidget(self.steam_auto_path_btn)
        steam_folder_layout.addWidget(self.select_steam_folder_btn)

        
        self.set_steam_folder_path()
      
        # --- Game ID selection ---
        game_id_layout = QHBoxLayout()
        self.game_id_edit = QLineEdit()
        self.game_id_edit.setPlaceholderText(self.translations.get("game_id_label"))
        self.game_id_edit.textChanged.connect(lambda text: self.settings.setValue("LastEnteredID", text))
        self.load_game_btn = QPushButton(self.translations.get("get_ach"))
        self.load_game_btn.clicked.connect(self.load_steam_game_stats)
        self.clear_game_id = QPushButton(self.translations.get("clear_and_paste"))
        self.clear_game_id.pressed.connect(lambda: ( 
            self.game_id_edit.clear(),
            self.game_id_edit.setText(QApplication.clipboard().text()),
            self.handle_game_id_action()
        ))
        game_id_layout.addWidget(self.game_id_edit)
        game_id_layout.addWidget(self.load_game_btn)
        game_id_layout.addWidget(self.clear_game_id)

        
        # --- Frame ---
        steam_group_layout = QVBoxLayout()
        steam_group_layout.addLayout(steam_folder_layout)
        steam_group_layout.addLayout(game_id_layout)
        self.steam_group = QGroupBox(self.translations.get("indirect_file_sel_label"))
        self.steam_group.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.steam_group.setLayout(steam_group_layout)
        file_search_layout.addWidget(self.steam_group)
        
        # Set layout for collapsible section
        self.file_search_section.setLayout(file_search_layout)
        self.layout.addWidget(self.file_search_section)
        

       
        
        # --- Language selection and info ---
        self.lang_layout = QHBoxLayout()

        # 1. Translation language selection (only for non-Ukrainian/Polish UI)
        self.translation_lang_label = None
        self.translation_lang_combo = None
        
        # Vertical separator creation
        self.translation_separator = QFrame()
        self.translation_separator.setFrameShape(QFrame.Shape.VLine)
        self.translation_separator.setFrameShadow(QFrame.Shadow.Sunken)

        if self.language == 'English':
            self.translation_lang_label = QLabel(self.translations.get("translation_lang", "Translation:"))
            self.lang_layout.addWidget(self.translation_lang_label)
            
            self.translation_lang_combo = QComboBox()
            available_languages = get_available_languages_for_selection()
            system_lang = get_system_language()
            
            # Add languages to combo box with display names
            for lang_code in available_languages:
                display_name = get_display_name(lang_code)
                self.translation_lang_combo.addItem(display_name, lang_code)
            
            # Set system language as default
            default_index = 0
            for i in range(self.translation_lang_combo.count()):
                if self.translation_lang_combo.itemData(i) == system_lang:
                    default_index = i
                    break
            self.translation_lang_combo.setCurrentIndex(default_index)
            
            self.translation_lang_combo.currentTextChanged.connect(self.on_translation_language_changed)
            self.lang_layout.addWidget(self.translation_lang_combo)
        else:
            # Hide separator for non-English UI languages
            self.translation_separator.setVisible(False)

        # Vertical separator
        self.lang_layout.addWidget(self.translation_separator)


        # 2. Game name
        self.gamename_label = QLabel(
            f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
        self.lang_layout.addWidget(self.gamename_label)

        # Vertical separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.VLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        self.lang_layout.addWidget(line2)

        # 3. File version
        self.version_label = QLabel(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
        self.lang_layout.addWidget(self.version_label)

        # Vertical separator
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.VLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        self.lang_layout.addWidget(line3)

        # 4. Achievement number
        self.countby2 = self.translations.get('unknown')
        self.ach_number = QLabel(f"{self.translations.get('ach_number')}{self.countby2}")
        self.lang_layout.addWidget(self.ach_number)


        # --- Frame ---
        box = QGroupBox("")
        box.setFlat(False)
        box.setLayout(self.lang_layout)
        self.layout.addWidget(box)


        
        # -- Undo/Redo ---
        self.undo_stack = []
        self.redo_stack = []
        self.is_undoing = False
        self.is_redoing = False
        self.is_manual_resizing = False
        

        # --- Table ---
        self.table = QTableWidget()
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.itemChanged.connect(self.on_table_item_changed)

        # --- Context Menu for Copy/Paste/Cut/Delete/Redo ---
        self.copy_action = QAction(self.translations.get("copy", "Copy"), self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(self.copy_selection_to_clipboard)

        self.paste_action = QAction(self.translations.get("paste", "Paste"), self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.triggered.connect(self.paste_from_clipboard)

        self.cut_action = QAction(self.translations.get("cut", "Cut"), self)
        self.cut_action.setShortcut("Ctrl+X")
        self.cut_action.triggered.connect(self.cut_selection_to_clipboard)

        self.delete_action = QAction(self.translations.get("delete", "Delete"), self)
        self.delete_action.setShortcut("Delete")
        self.delete_action.triggered.connect(self.clear_selection)
        
        self.redo_action = QAction(self.translations.get("redo", "Redo"), self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.redo)

        self.undo_action = QAction(self.translations.get("undo", "Undo"), self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.undo)


        # Set context menu policy and add actions
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.table.addAction(self.undo_action)
        self.table.addAction(self.redo_action)
        self.table.addAction(self.copy_action)
        self.table.addAction(self.paste_action)
        self.table.addAction(self.cut_action)
        self.table.addAction(self.delete_action)
        


        self.layout.addWidget(self.table)
        
        self.header = self.table.horizontalHeader()
        self.header.setStretchLastSection(False)

        self.data_rows = []
        self.headers = []
        self.raw_data = b""
        self.chunks = []
        

        stored_path = self.settings.value("UserSteamPath", "")
        if not isinstance(stored_path, str):
            stored_path = ""

        if not stored_path.strip():
            stored_path = self.default_steam_path
            self.settings.setValue("UserSteamPath", stored_path)
            self.settings.sync()

        self.steam_folder_path.setText(stored_path)
        self.steam_folder = self.steam_folder_path.text().strip()        
        self.game_id_edit.setText(self.settings.value("LastEnteredID", ""))
        self.stats_bin_path_path.setText(self.settings.value("LastEnteredFilePath", ""))
        
        self.configs = {
            self.steam_folder_path: {"key": "UserSteamPath", "default": self.default_steam_path},
            self.game_id_edit: {"key": "LastEnteredID", "default": ""},
            self.stats_bin_path_path: {"key": "LastEnteredFilePath", "default": ""}
        }
        

        # --- Load settings ---
        for obj, items in self.configs.items():
            if self.settings.value(items["key"]):
                obj.setText(self.settings.value(items["key"]))
            else:
                obj.setText(items["default"])
                self.settings.setValue(items["key"], items["default"])

        # Replace in column action
        self.replace_in_column_action = QAction(self.translations.get("search_replace", "Search and Replace"), self)
        self.replace_in_column_action.setShortcut("Ctrl+F")
        self.replace_in_column_action.triggered.connect(self.show_find_replace_dialog)
        self.table.addAction(self.replace_in_column_action)

        # Highlight delegate for search
        self.highlight_delegate = HighlightDelegate(self.table)
        self.table.setItemDelegate(self.highlight_delegate)

        # Add find/replace panel (hidden by default)
        self.find_replace_panel = FindReplacePanel(self, self.headers)
        self.layout.addWidget(self.find_replace_panel)
        # Initialize theme manager
        self.theme_manager = ThemeManager(self)

        # Create menubar
        self.create_menubar()
        
        # Apply initial font settings
        self.theme_manager.apply_font_to_widgets()
        
        # Ensure UI texts are properly set with selected language
        # This is important for first run when language is selected
        if hasattr(self, 'translations') and self.translations:
            self.refresh_ui_texts(update_menubar=False)  # Menu already created above

    def create_menubar(self):
        """Create menubar using ui_builder plugin"""
        # Initialize ui_builder with current translations
        self.ui_builder = UIBuilder(self, self.translations)
        menubar = self.ui_builder.create_menubar()
        
        # Adding menubar to the layout
        self.setMenuWidget(menubar)

    def set_window_size(self):
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()
        screen_width = geometry.width()
        screen_height = geometry.height()

        width = int(screen_width * 0.7)
        height = int(screen_height * 0.8)

        width = max(width, self.minimumWidth())
        height = max(height, self.minimumHeight())

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.setGeometry(x, y, width, height)

    def stretch_columns(self):
        """Stretch columns to fill available width while respecting minimum widths"""
        if not self.table or self.table.columnCount() == 0:
            return

        header = self.table.horizontalHeader()
        total_width = self.table.viewport().width()
        visible_columns = [col for col in range(self.table.columnCount()) if not self.table.isColumnHidden(col)]
        
        if not visible_columns:
            return

        # Calculate minimum width for each column based on header text
        font_metrics = header.fontMetrics()
        min_widths = []
        for col in visible_columns:
            header_text = self.table.horizontalHeaderItem(col).text() if self.table.horizontalHeaderItem(col) else ""
            # Add padding (20px for margins/padding)
            text_width = font_metrics.horizontalAdvance(header_text) + 20
            # Use maximum of 120px or header width
            min_widths.append(max(text_width, 120))

        total_min_width = sum(min_widths)
        
        if total_width > total_min_width:
            # Distribute extra space proportionally
            extra_space = total_width - total_min_width
            space_per_column = extra_space // len(visible_columns)
            
            for i, col in enumerate(visible_columns):
                new_width = min_widths[i] + space_per_column
                self.table.setColumnWidth(col, new_width)
        else:
            # Just use minimum widths
            for i, col in enumerate(visible_columns):
                self.table.setColumnWidth(col, min_widths[i])
        
        # Set resize mode for all columns (visible and hidden)
        for i in range(self.table.columnCount()):
            self.header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

    def resizeEvent(self, event):
        self.stretch_columns()
        super().resizeEvent(event)

    def set_steam_folder_path(self, force=False):
        path = self.settings.value("UserSteamPath", "") or ""
        if force or not path.strip():
            detected = self.detect_steam_path()
            if detected:
                path = detected
            else:
                if sys.platform == "win32":
                    fallback = "C:\\Program Files (x86)\\Steam"
                    if os.path.exists(fallback):
                        path = fallback
                    else:
                        QMessageBox.warning(self, self.translations.get("attention"), self.translations.get("folder_not_found_auto"))
                        path = ""
                else:
                    path = ""
            self.settings.setValue("UserSteamPath", path)
            self.settings.sync()

        self.steam_folder_path.setText(path)
    
    def steam_auto_forcing(self):
        path =  self.detect_steam_path()
        self.settings.setValue("UserSteamPath", path)
        self.settings.sync()
        self.steam_folder_path.setText(path)


    def on_steam_path_changed(self, text):
        # Update steam folder path when text changes
        self.steam_folder = text.strip()
        self.settings.setValue("UserSteamPath", self.steam_folder)
        self.settings.sync()

    def set_column_visible(self, header, visible):
        try:
            col = self.headers.index(header)
            self.table.setColumnHidden(col, not visible)        
        except ValueError:
            pass

    # =================================================================
    # LANGUAGE AND LOCALIZATION
    # =================================================================

    def change_language(self, lang):
        self.settings.setValue("language", lang)
        self.settings.sync()
        self.language = lang
        self.translations = self.load_language(lang)
        # Reinitialize ui_builder with new translations
        if hasattr(self, 'ui_builder'):
            self.ui_builder = UIBuilder(self, self.translations)
        
        # Update visibility of translation controls based on new language
        self.update_translation_controls_visibility()
        
        self.refresh_ui_texts()
        
        # Refresh the table if it exists and we have data
        if hasattr(self, 'parse_and_fill_table') and hasattr(self, 'raw_data') and self.raw_data:
            self.parse_and_fill_table()
    
    def update_translation_controls_visibility(self):
        """Update visibility of translation language controls based on current UI language"""
        # Show translation controls only for English UI language
        show_translation_controls = self.language == 'English'
        
        # Update separator visibility
        if hasattr(self, 'translation_separator'):
            self.translation_separator.setVisible(show_translation_controls)
        
        if show_translation_controls:
            # Create translation controls if they don't exist
            if not hasattr(self, 'translation_lang_label') or not self.translation_lang_label:
                from plugins.steam_lang_codes import get_available_languages_for_selection, get_display_name, get_system_language
                
                self.translation_lang_label = QLabel(self.translations.get("translation_lang", "Translation:"))
                # Insert at position 0 (beginning)
                self.lang_layout.insertWidget(0, self.translation_lang_label)
                
                self.translation_lang_combo = QComboBox()
                available_languages = get_available_languages_for_selection()
                system_lang = get_system_language()
                
                # Add languages to combo box with display names
                for lang_code in available_languages:
                    display_name = get_display_name(lang_code)
                    self.translation_lang_combo.addItem(display_name, lang_code)
                
                # Set system language as default
                default_index = 0
                for i in range(self.translation_lang_combo.count()):
                    if self.translation_lang_combo.itemData(i) == system_lang:
                        default_index = i
                        break
                self.translation_lang_combo.setCurrentIndex(default_index)
                
                self.translation_lang_combo.currentTextChanged.connect(self.on_translation_language_changed)
                # Insert at position 1 (after label)
                self.lang_layout.insertWidget(1, self.translation_lang_combo)
            else:
                # Show existing controls
                self.translation_lang_label.setVisible(True)
                self.translation_lang_combo.setVisible(True)
        else:
            # Hide controls for non-English UI languages
            if hasattr(self, 'translation_lang_label') and self.translation_lang_label:
                self.translation_lang_label.setVisible(False)
            if hasattr(self, 'translation_lang_combo') and self.translation_lang_combo:
                self.translation_lang_combo.setVisible(False)

    def load_language(self, language):
        """Load language file using new locale system"""
        return load_translations_for_language(language)

    def refresh_ui_texts(self, update_menubar=True):
        self.setWindowTitle(f"{self.translations.get('app_title')}{APP_VERSION}")
        self.stats_bin_path_path.setPlaceholderText(self.translations.get("man_select_file_label"))
        self.stats_bin_path_btn.setText(self.translations.get("man_select_file"))
        self.select_stats_bin_path_btn.setText(self.translations.get("get_ach"))
        self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
        self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
        self.steam_folder_path.setPlaceholderText(self.translations.get("steam_folder_label"))
        self.select_steam_folder_btn.setText(self.translations.get("select_steam_folder"))
        self.steam_auto_path_btn.setText(self.translations.get("auto"))
        self.game_id_edit.setPlaceholderText(self.translations.get("game_id_label"))
        self.load_game_btn.setText(self.translations.get("get_ach"))
        self.clear_game_id.setText(self.translations.get("clear_and_paste"))
        self.abo_label.setText(self.translations.get("OR"))
        self.steam_group.setTitle(self.translations.get("indirect_file_sel_label"))
        self.stats_group.setTitle(self.translations.get("man_file_sel_label"))
        
        # Update file search section title based on state
        if hasattr(self, 'file_search_section'):
            if self.file_search_section.isChecked():
                self.file_search_section.setTitle(self.translations.get("file_search_section_expanded", "▼ File Search"))
            else:
                self.file_search_section.setTitle(self.translations.get("file_search_section_collapsed", "▶ File Search"))
        # Update translation language label if exists and visible
        if hasattr(self, 'translation_lang_label') and self.translation_lang_label and self.translation_lang_label.isVisible():
            self.translation_lang_label.setText(self.translations.get("translation_lang"))
        
        if self.countby2 is int:
            self.ach_number.setText(f"{self.translations.get('ach_number')}{self.countby2}")

        else:
            self.ach_number.setText(f"{self.translations.get('ach_number')}{self.translations.get('unknown')}")

        self.copy_action.setText(self.translations.get("copy", "Copy"))
        self.paste_action.setText(self.translations.get("paste", "Paste"))
        self.cut_action.setText(self.translations.get("cut", "Cut"))
        self.delete_action.setText(self.translations.get("delete", "Delete"))
        self.redo_action.setText(self.translations.get("redo", "Redo"))
        self.undo_action.setText(self.translations.get("undo", "Undo"))
        self.replace_in_column_action.setText(self.translations.get("replace_in_column", "Replace"))
        if hasattr(self, 'global_search_line') and self.global_search_line is not None:
            self.global_search_line.setPlaceholderText(self.translations.get("in_column_search_placeholder"))
        
        # Update find/replace panel translations
        if hasattr(self, 'find_replace_panel'):
            self.find_replace_panel.update_translations(self.translations)
        
        self.create_menubar()
        
        # Update theme and font checkboxes after recreating menubar
        if hasattr(self, 'theme_manager'):
            current_theme = self.theme_manager.get_current_theme()
            for theme, action in getattr(self, "theme_actions", {}).items():
                action.setChecked(theme == current_theme)
                
            current_weight = self.theme_manager.get_current_font_weight()
            for weight, action in getattr(self, "font_actions", {}).items():
                action.setChecked(weight == current_weight)
                
            current_size = self.theme_manager.get_current_font_size()
            for size, action in getattr(self, "font_size_actions", {}).items():
                action.setChecked(size == current_size)
        
        for header, action in getattr(self, "column_actions", {}).items():
            col = self.headers.index(header)
            action.setChecked(not self.table.isColumnHidden(col))
        self.version()
        self.gamename()
        # Apply fonts to all widgets
        if hasattr(self, 'theme_manager'):
            self.theme_manager.apply_font_to_widgets()
        if update_menubar:
            self.create_menubar()


    # =================================================================
    # FILE OPERATIONS AND STEAM INTEGRATION
    # =================================================================

    def game_id(self):
        """Parse game ID using steam integration plugin"""
        text = self.game_id_edit.text().strip()
        return self.steam_integration.parse_game_id(text)

    def select_steam_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.translations.get("select_steam_folder"), self.steam_folder
        )
        if folder:
            real_path = os.path.realpath(folder)
            self.steam_folder_path.setText(real_path)
            self.settings.setValue("UserSteamPath", real_path)
            self.settings.sync()  

    def load_steam_game_stats(self):
        self.force_manual_path = False
        game_id = self.game_id()
        if not game_id:
            QMessageBox.warning(self, self.translations.get("error"), self.translations.get("error_no_id"))
            return
        if not self.steam_folder:
            QMessageBox.warning(self, self.translations.get("error"), self.translations.get("error_no_path"))
            return
        path = self.get_stats_bin_path()
        try:
            with open(path, "rb") as f:
                self.raw_data = f.read()
        except FileNotFoundError:
            QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_no_file')}{path}")
            return
        except Exception as e:
            QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_cannot_open')}{e}")
            return
        
        self.parse_and_fill_table()
        self.version()
        self.gamename()

    def parse_and_fill_table(self):
        # Check if we have data to parse
        if not hasattr(self, 'raw_data') or not self.raw_data:
            return
        
        # Use binary parser plugin
        all_rows, headers = self.binary_parser.parse_binary_data(self.raw_data)
        self.chunks = self.binary_parser.chunks
        self.headers = self.prioritize_headers(headers)  # Prioritize headers
        
        self.data_rows = all_rows
        self.table.clear()
        self.table.setColumnCount(len(self.headers))
        
        # Create header labels with Steam language display names
        header_labels = []
        for header in self.headers:
            if header == 'key':
                header_labels.append(header.upper())
            else:
                # Use Steam language display name if available
                display_name = get_display_name(header)
                # Add line break before parentheses for better readability
                if '(' in display_name:
                    display_name = display_name.replace(' (', '\n(')
                header_labels.append(display_name)
        
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.setRowCount(len(all_rows))
        
        # Ensure all rows have columns for our headers
        for row in self.data_rows:
            for header in self.headers:
                if header not in row:
                    row[header] = ''
        
        # Fill table with data
        self.table.blockSignals(True)
        for row_i, row in enumerate(self.data_rows):
            for col_i, col_name in enumerate(self.headers):
                value = row.get(col_name, '')

                item = QTableWidgetItem(value)
                if col_name == 'key':
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.table.setItem(row_i, col_i, item)
        self.table.blockSignals(False)
        
        self.stretch_columns()
        self.update_row_heights()
        self.create_menubar()
        self.version()
        self.gamename()
        self.countby2 = len(all_rows)//2
        self.ach_number.setText(f"{self.translations.get('ach_number')}{self.countby2}")
        
        # Collapse file search section after loading table
        if hasattr(self, 'file_search_section'):
            self.file_search_section.setChecked(False)
        
        msg = self.translations.get("records_loaded").format(count=len(all_rows), countby2=self.countby2)
        QMessageBox.information(self, self.translations.get("success"), msg)

    def replace_lang_in_bin(self):
        """Replace language data in binary using file_manager plugin"""
        file_path = self.get_stats_bin_path()
        try:
            data = self.file_manager.load_binary_file(file_path)
            return self.file_manager.replace_language_in_binary(data, self.data_rows)
        except Exception as e:
            # If direct file loading fails, use raw_data if available
            if hasattr(self, 'raw_data') and self.raw_data:
                return self.file_manager.replace_language_in_binary(self.raw_data, self.data_rows)
            return None

    def export_bin(self):
        """Open file in explorer using steam integration plugin"""
        filepath = os.path.abspath(self.get_stats_bin_path())
        if not os.path.isfile(filepath):
            QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_no_file')}{filepath}")
            return
        
        if not self.steam_integration.open_file_in_explorer(filepath):
            QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_cannot_open')}")

    def save_bin_unknow(self):
        # Save to Steam folder
        # First, check if game_id is available
        game_id = self.current_game_id()
        if not game_id:
            # Create custom warning message box
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(self.translations.get("error"))
            msg_box.setText(self.translations.get("save_no_game_id", 
                "Cannot save to Steam: Game ID is not specified. Please enter a Game ID or select a game from the list."))
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        self.sync_table_to_data_rows()
        datas = self.replace_lang_in_bin()
        if datas is None:
            # Create custom warning message box
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(self.translations.get("error"))
            msg_box.setText(self.translations.get("error_no_data_to_save"))
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return

        save_path = os.path.join(
            self.steam_folder,
            "appcache",
            "stats",
            f"UserGameStatsSchema_{game_id}.bin"
        )

        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(datas)
            
            # Create custom message box with proper button text
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle(self.translations.get("success"))
            msg_box.setText(self.translations.get("in_steam_folder_saved"))
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            
            self.set_modified(False)
        except Exception as e:
            # Create custom error message box with error details
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(self.translations.get("error"))
            msg_box.setText(f"{self.translations.get('error_cannot_save')}\n{str(e)}")
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()

    def save_bin_know(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            self.translations.get("file_saving_file_dialog"),
            self.get_stats_bin_path(),
            "Binary files (*.bin);;All files (*)"
        )

        if not save_path:
            return
        self.sync_table_to_data_rows()
        datas = self.replace_lang_in_bin()
        if datas is None:
            # Create custom warning message box
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(self.translations.get("error"))
            msg_box.setText(self.translations.get("error_no_data_to_save"))
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return

        try:
            with open(save_path, "wb") as f:
                f.write(datas)
            
            # Create custom success message box
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle(self.translations.get("success"))
            msg_box.setText(self.translations.get("file_saved").format(save_path=save_path))
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
        except Exception as e:
            # Create custom error message box with error details
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(self.translations.get("error"))
            msg_box.setText(f"{self.translations.get('error_cannot_save')}\n{str(e)}")
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()

    def detect_steam_path(self):
        """Auto-detect Steam path using steam integration plugin"""
        return self.steam_integration.detect_steam_path()

    def get_stats_bin_path(self):
       # Determine path to UserGameStatsSchema_{game_id}.bin
        manual_path = self.stats_bin_path_path.text().strip()
        if self.force_manual_path and manual_path:
            return manual_path

        return os.path.abspath(
            os.path.join(
                self.steam_folder, "appcache", "stats",
                f"UserGameStatsSchema_{self.game_id()}.bin"
            )
        )
 
    def stats_bin_path_search(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            self.translations.get("man_select_file_file_dialog"),
            "",
            "Binary files (*.bin);;All files (*)"
        )
        if file:  # if user selected a file
            self.stats_bin_path_path.setText(file)
            self.select_stats_bin_path()

    def select_stats_bin_path(self):
        path = self.stats_bin_path_path.text().strip()
        if not path:
            QMessageBox.warning(self, self.translations.get("error"), self.translations.get("error_UserGameStatsSchema_sel"))
            return
        try:
            with open(path, "rb") as f:
                self.raw_data = f.read()
        except Exception as e:
            QMessageBox.critical(self, self.translations.get("error"), f"{self.translations.get('error_cannot_open')}{e}")
            return

        # Activate manual path usage
        self.force_manual_path = True

        # Try to extract game_id from filename
        import re
        m = re.search(r'UserGameStatsSchema_(\d+)\.bin$', path)
        if m:
            self.game_id_edit.setText(m.group(1))

        self.parse_and_fill_table()
        self.version()
        self.gamename()

    def use_manual_path(self):
        self.force_manual_path = True

    def use_steam_path(self):
        self.force_manual_path = False
        self.set_steam_folder_path(force=True)

    def delete_current_stats_file(self):
        # Check if file exists
        path = self.get_stats_bin_path()
        if not os.path.isfile(path):
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle(self.translations.get("error", "Error"))
            box.setText(f"{self.translations.get('error_no_file')}{path}")
            btn_close = box.addButton(self.translations.get("close", "Close"), QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_close)
            box.exec()
            return

        confirm_text = self.translations.get(
            "delete_stats_file_confirm"
        ).format(path=path)
        
        done_msg = self.translations.get(
            "delete_stats_file_done"
        ).format(gamename=self.gamename())

        # Confirmation dialog
        confirm_box = QMessageBox(self)
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setWindowTitle(self.translations.get("delete_stats_file"))
        confirm_box.setText(confirm_text)
        btn_CSV = confirm_box.addButton(self.translations.get(
            "CSV", "Want to save CSV"), QMessageBox.ButtonRole.ActionRole)
        btn_yes = confirm_box.addButton(self.translations.get("yes", "Yes"), QMessageBox.ButtonRole.YesRole)
        btn_no = confirm_box.addButton(self.translations.get("no", "No"), QMessageBox.ButtonRole.NoRole)
        confirm_box.setDefaultButton(btn_no)
        confirm_box.exec()
        if confirm_box.clickedButton() is btn_no:
            return
        if confirm_box.clickedButton() is btn_yes:
            self.export_csv_all()

        # Deleting the file
        try:
            os.remove(path)
        except Exception as e:
            err_box = QMessageBox(self)
            err_box.setIcon(QMessageBox.Icon.Critical)
            err_box.setWindowTitle(self.translations.get("error", "Error"))
            err_box.setText(
                self.translations.get(
                    "delete_stats_file_failed",
                    "Cannot delete file: {error}"
                ).format(error=e)
            )
            btn_close3 = err_box.addButton(self.translations.get("close", "Close"), QMessageBox.ButtonRole.RejectRole)
            err_box.setDefaultButton(btn_close3)
            err_box.exec()
            return

        # Reset UI
        self.raw_data = b""
        self.data_rows = []
        self.headers = []
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        if hasattr(self, "version_label"):
            self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
        if hasattr(self, "gamename_label"):
            self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
        self.set_modified(False)

        ok_box = QMessageBox(self)
        ok_box.setIcon(QMessageBox.Icon.Information)
        ok_box.setWindowTitle(self.translations.get("success", "Success"))
        ok_box.setText(done_msg)
        btn_close4 = ok_box.addButton(self.translations.get("close", "Close"), QMessageBox.ButtonRole.AcceptRole)
        ok_box.setDefaultButton(btn_close4)
        ok_box.exec()

    # =================================================================
    # CSV OPERATIONS
    # =================================================================

    def export_csv_all(self):
        """Export all data to CSV using csv_handler plugin"""
        fname, _ = QFileDialog.getSaveFileName(self, self.translations.get("export_csv_all_file_dialog"), '', 'CSV Files (*.csv)')
        if not fname:
            return
        
        try:
            self.csv_handler.export_all_data(self.data_rows, self.headers, fname)
            QMessageBox.information(self, self.translations.get("success"), self.translations.get("csv_saved"))
        except Exception as e:
            QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_cannot_save')}{e}")

    def export_csv_for_translate(self):
        """Export data for translation using csv_handler plugin"""
        if 'english' not in self.headers:
            QMessageBox.warning(self, self.translations.get("error"), self.translations.get("error_no_english"))
            return
            
        info_text = self.translations.get("export_csv_for_translate_info", "")
        dlg = ContextLangDialog(self.headers, info_text=info_text, mode='export', parent=self)
        if not dlg.exec():
            return
            
        params = dlg.get_selected()
        context_col = params["context_col"]

        fname, _ = QFileDialog.getSaveFileName(self,self.translations.get("export_csv_all_file_dialog"), "", "CSV Files (*.csv)")
        if not fname:
            return
        
        try:
            self.csv_handler.export_for_translation(self.data_rows, context_col, fname)
            QMessageBox.information(self, self.translations.get("success"), self.translations.get("csv_saved"))
        except Exception as e:
            QMessageBox.warning(self, self.translations.get("error"), str(e))

    def import_csv(self):
        """Import translations using csv_handler plugin"""
        info_text = self.translations.get("import_csv_info", "")
        dlg = ContextLangDialog(self.headers, info_text=info_text, mode='import', parent=self)
        if not dlg.exec():
            return
            
        params = dlg.get_selected()
        import_col = params["context_col"]

        fname, _ = QFileDialog.getOpenFileName(self, self.translations.get("import_csv_file_dialog"), "", "CSV Files (*.csv)")
        if not fname:
            return

        try:
            success, imported_count, changed_count, skipped_count, reason = self.csv_handler.import_translations(
                fname, self.data_rows, import_col
            )
            
            if success:
                if changed_count > 0:
                    self.refresh_table()
                    details = self.translations.get("import_details", 
                        "Imported: {imported}, Changed: {changed}, Skipped: {skipped}").format(
                        imported=imported_count, changed=changed_count, skipped=skipped_count
                    )
                    QMessageBox.information(self, self.translations.get("success"), details)
                    self.set_modified(True)
                else:
                    # No changes made
                    msg = self.translations.get("import_no_changes", "CSV imported, but no data was changed")
                    if reason:
                        msg += f"\n{self.translations.get('reason', 'Reason')}: {reason}"
                    QMessageBox.information(self, self.translations.get("info"), msg)
            else:
                # Import failed
                error_msg = self.translations.get("import_failed", "Import failed")
                if reason:
                    error_msg += f"\n{reason}"
                QMessageBox.warning(self, self.translations.get("error"), error_msg)
        except Exception as e:
            QMessageBox.warning(self, self.translations.get("error"), 
                              f"{self.translations.get('import_failed', 'Import failed')}\n{str(e)}")

    # =================================================================
    # TABLE OPERATIONS AND DATA MANAGEMENT
    # =================================================================

    def refresh_table(self):
        self.table.clear()
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(len(self.data_rows))
        for row_i, row_data in enumerate(self.data_rows):
            for col_i, header in enumerate(self.headers):
                value = row_data.get(header, '')
                item = QTableWidgetItem(value)
                self.table.setItem(row_i, col_i, item)
        self.update_row_heights()

    def on_table_item_changed(self, item):
        if self.is_undoing or self.is_redoing:
            return

        row = item.row()
        col = item.column()
        header = self.headers[col]
        new_value = item.text()
        if 0 <= row < len(self.data_rows):
            old_value = self.data_rows[row].get(header, '')
            self.undo_stack.append((row, col, header, old_value, new_value))
            self.redo_stack.clear() 
            self.data_rows[row][header] = new_value
        self.set_modified(True)
        
        # Update row height to accommodate wrapped text
        # This allows text to wrap down instead of expanding the column horizontally
        if hasattr(self, 'update_row_heights'):
            # Update only the affected row for performance
            max_height = self.table.verticalHeader().defaultSectionSize()
            has_content = False
            
            for col_i in range(self.table.columnCount()):
                cell_item = self.table.item(row, col_i)
                if cell_item and cell_item.text():
                    has_content = True
                    doc = QTextDocument()
                    doc.setHtml(cell_item.text())
                    doc.setTextWidth(self.table.columnWidth(col_i))
                    height = doc.size().height() + 8
                    if height > max_height:
                        max_height = height
            
            # Only set custom height if there's actual content, otherwise use default
            if has_content:
                self.table.setRowHeight(row, int(max_height))
            else:
                self.table.setRowHeight(row, self.table.verticalHeader().defaultSectionSize())

    def sync_table_to_data_rows(self):

        if self.table.state() == QAbstractItemView.State.EditingState:
            editor = self.table.focusWidget()
            if editor:

                index = self.table.indexAt(editor.pos())
                if index.isValid():

                    self.table.model().setData(index, editor.text())

                self.table.closePersistentEditor(self.table.item(index.row(), index.column()))


        # Sync changes from table widget back to data_rows
        for row_i in range(self.table.rowCount()):
            if row_i >= len(self.data_rows):
                continue
            for col_i, header in enumerate(self.headers):
                item = self.table.item(row_i, col_i)
                value = item.text() if item else ''
                self.data_rows[row_i][header] = value

    def global_search_in_table(self, text):
        search_text = text.strip().lower()

        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
                               
        if not search_text:
            self.highlight_delegate.set_highlight("")
            self.highlight_delegate.highlight_column = -1
            self.table.viewport().update()
            return

        self.highlight_delegate.set_highlight(search_text)
        self.highlight_delegate.highlight_column = -1 
        self.table.viewport().update()

        for row in range(self.table.rowCount()):
            row_has_match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    row_has_match = True
            self.table.setRowHidden(row, not row_has_match)

    def update_row_heights(self):
        for row in range(self.table.rowCount()):
            max_height = self.table.verticalHeader().defaultSectionSize()
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and item.text():
                    doc = QTextDocument()
                    doc.setHtml(item.text())
                    doc.setTextWidth(self.table.columnWidth(col))
                    height = doc.size().height() + 8
                    if height > max_height:
                        max_height = height
            self.table.setRowHeight(row, int(max_height))

    # =================================================================
    # EDITING OPERATIONS (UNDO/REDO/COPY/PASTE)
    # =================================================================

    def copy_selection_to_clipboard(self):
        selection = self.table.selectedRanges()
        if not selection:
            return
        s = ''
        for rng in selection:
            for row in range(rng.topRow(), rng.bottomRow()+1):
                row_data = []
                for col in range(rng.leftColumn(), rng.rightColumn()+1):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else '')
                s += '\t'.join(row_data) + '\n'
        QApplication.clipboard().setText(s)

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return
        rows = clipboard.split('\n')
        current = self.table.currentRow()
        col = self.table.currentColumn()
        for r, row_data in enumerate(rows):
            if not row_data.strip():
                continue
            for c, text in enumerate(row_data.split('\t')):
                row_idx = current + r
                col_idx = col + c
                if row_idx < self.table.rowCount() and col_idx < self.table.columnCount():
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(text))

    def cut_selection_to_clipboard(self):
        self.copy_selection_to_clipboard()
        self.clear_selection()

    def clear_selection(self):
        selected_ranges = self.table.selectedRanges()
        for rng in selected_ranges:
            for row in range(rng.topRow(), rng.bottomRow() + 1):
                for col in range(rng.leftColumn(), rng.rightColumn() + 1):
                    item = self.table.item(row, col)
                    if item:
                        item.setText("")  
                    else:
                        self.table.setItem(row, col, QTableWidgetItem(""))

                    if 0 <= row < len(self.data_rows) and 0 <= col < len(self.headers):
                        header = self.headers[col]
                        self.data_rows[row][header] = ""

    def undo(self):
        if not self.undo_stack:
            return
        self.is_undoing = True
        row, col, header, old_value, new_value = self.undo_stack.pop()
        self.data_rows[row][header] = old_value
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem(old_value)
            self.table.setItem(row, col, item)
        else:
            item.setText(old_value)
        self.redo_stack.append((row, col, header, new_value, old_value))
        self.is_undoing = False

    def redo(self):
        if not self.redo_stack:
            return
        self.is_redoing = True
        row, col, header, new_value, old_value = self.redo_stack.pop()
        self.data_rows[row][header] = new_value
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem(new_value)
            self.table.setItem(row, col, item)
        else:
            item.setText(new_value)
        self.undo_stack.append((row, col, header, old_value, new_value))
        self.is_redoing = False

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Undo):
            self.undo()
            event.accept()
        else:
            super().keyPressEvent(event)

    # =================================================================
    # UTILITY FUNCTIONS
    # =================================================================

    def prioritize_headers(self, headers):
        """
        Prioritize headers with translation column after key:
        - Ukrainian UI: key > ukrainian > english > others
        - Polish UI: key > polish > english > others  
        - Other UI: key > selected translation language > english > others
        The translation column will use existing data if available.
        """
        headers = [h for h in headers if h != 'key']
        prioritized = ['key']
        
        # Determine translation language based on UI or user selection
        # Create mapping from UI language to Steam language code
        ui_to_steam_lang = {
            'Українська': 'ukrainian',
            'Polski': 'polish'
        }
        
        if self.language in ui_to_steam_lang:
            translation_lang = ui_to_steam_lang[self.language]
        else:
            # For English and other UI languages, get selected language from combo box
            if hasattr(self, 'translation_lang_combo') and self.translation_lang_combo:
                translation_lang = self.translation_lang_combo.currentData()
            else:
                translation_lang = get_system_language()
        
        # Add translation column (prefer existing data column)
        if translation_lang and translation_lang != 'english':
            if translation_lang in headers:
                # Use existing column with this code
                prioritized.append(translation_lang)
                headers.remove(translation_lang)
            else:
                # Check if there's a related existing column
                # Common mappings for similar languages
                related_mappings = {
                    'spanish': 'latam',  # If user selects spanish, use latam if available
                    'latam': 'spanish',  # If user selects latam, use spanish if available
                }
                
                related_lang = related_mappings.get(translation_lang)
                if related_lang and related_lang in headers:
                    prioritized.append(related_lang)
                    headers.remove(related_lang)
                else:
                    # Use selected language even if no existing data
                    prioritized.append(translation_lang)
                
        # Always add english after translation
        if 'english' in headers:
            prioritized.append('english')
            headers.remove('english')
        
        # Sort remaining headers alphabetically
        return prioritized + sorted(headers)
    
    def on_translation_language_changed(self):
        """Handle translation language change"""
        if not hasattr(self, 'data_rows') or not self.data_rows:
            return
            
        # Remove empty columns before creating new ones
        self.remove_empty_columns()
            
        # Re-prioritize headers and refresh table
        if hasattr(self, 'headers') and self.headers:
            old_headers = self.headers.copy()
            
            # Get all original headers from binary data
            all_headers = set()
            for row in self.data_rows:
                for col in row.keys():
                    all_headers.add(col)
            
            # Re-prioritize with new selection
            self.headers = self.prioritize_headers(list(all_headers))
            
            # Refresh table display
            self.refresh_table_with_new_headers()

    def refresh_table_with_new_headers(self):
        """Refresh table when headers change"""
        if not hasattr(self, 'data_rows') or not self.data_rows:
            return
            
        self.table.clear()
        self.table.setColumnCount(len(self.headers))
        
        # Create header labels with Steam language display names
        header_labels = []
        for header in self.headers:
            if header == 'key':
                header_labels.append(header.upper())
            else:
                display_name = get_display_name(header)
                header_labels.append(display_name)
        
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.setRowCount(len(self.data_rows))
        
        # Ensure all rows have columns for our headers
        for row in self.data_rows:
            for header in self.headers:
                if header not in row:
                    row[header] = ''
        
        # Fill table with data
        for row_i, row in enumerate(self.data_rows):
            for col_i, col_name in enumerate(self.headers):
                value = row.get(col_name, '')
                item = QTableWidgetItem(value)
                if col_name == 'key':
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.table.setItem(row_i, col_i, item)
        
        self.stretch_columns()
        self.update_row_heights()

    def remove_empty_columns(self):
        """Remove columns that are completely empty (except for key column)"""
        if not hasattr(self, 'data_rows') or not self.data_rows:
            return
        
        # Find columns to remove
        columns_to_remove = []
        
        # Get all column names from the data
        all_columns = set()
        for row in self.data_rows:
            all_columns.update(row.keys())
        
        for col_name in all_columns:
            # Never remove key column
            if col_name == 'key':
                continue
                
            # Check if column is completely empty
            is_empty = True
            for row in self.data_rows:
                value = row.get(col_name, '').strip()
                if value:  # If any non-empty value found
                    is_empty = False
                    break
            
            if is_empty:
                columns_to_remove.append(col_name)
        
        # Remove empty columns from data
        for col_name in columns_to_remove:
            for row in self.data_rows:
                if col_name in row:
                    del row[col_name]
        
        # Update headers list if it exists
        if hasattr(self, 'headers') and self.headers:
            self.headers = [h for h in self.headers if h not in columns_to_remove]

    def version(self):
        path = self.get_stats_bin_path()

        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            if hasattr(self, "version_label"):
                self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
            return None

        # Use binary parser plugin
        version_number = self.binary_parser.get_version(data)

        if hasattr(self, "version_label"):
            if version_number is not None:
                self.version_label.setText(f"{self.translations.get('file_version')}{version_number}")
            else:
                self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")

        return version_number

    def load_steam_game_names(self):
        """Load Steam game names from JSON file"""
        json_path = resource_path("assets/steam.api.allgamenames.json")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Create a dictionary mapping appid to name for fast lookup
                games_dict = {}
                for app in data.get('applist', {}).get('apps', []):
                    games_dict[str(app['appid'])] = app['name']
                return games_dict
        except Exception as e:
            print(f"Failed to load Steam game names: {e}")
            return {}
    
    def get_steam_game_name(self, appid):
        """Get game name from Steam API data by appid"""
        if not appid or not self.steam_game_names:
            return None
        return self.steam_game_names.get(str(appid))
    
    def on_steam_name_toggle(self, checked):
        """Handle toggle for Steam API name"""
        self.settings.setValue("UseSteamName", bool(checked))
        self.gamename()

    def gamename(self):
        path = self.get_stats_bin_path()

        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            if hasattr(self, "gamename_label"):
                self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
            return None

        # Use binary parser plugin
        name = self.binary_parser.get_gamename(data)
        
        # Check if we should use Steam API name instead
        if self.settings.value("UseSteamName", False, type=bool):
            game_id = self.game_id()
            if game_id:
                steam_name = self.get_steam_game_name(game_id)
                if steam_name:
                    name = steam_name

        if hasattr(self, "gamename_label"):
            self.gamename_label.setText(f"{self.translations.get('gamename')}{name if name else self.translations.get('unknown')}")

        return name

    def current_game_id(self):
        # Return game ID based on current mode (manual or steam path)
        if self.force_manual_path:
            manual_path = self.stats_bin_path_path.text().strip()
            import re
            m = re.search(r'UserGameStatsSchema_(\d+)\.bin$', manual_path)
            if m:
                return m.group(1)
        return self.game_id()

    def handle_game_id_action(self):
        game_id = self.game_id()
        if game_id:
            self.load_steam_game_stats()
        else:
            self.game_id_edit.clear()

    def on_file_search_section_toggled(self, checked):
        """Handle file search section collapse/expand"""
        if checked:
            # Expanded - show arrow down and content
            self.file_search_section.setTitle(self.translations.get("file_search_section_expanded", "▼ File Search"))
            # Restore normal height
            self.file_search_section.setMaximumHeight(16777215)  # Qt default max
            # Show all child widgets
            for i in range(self.file_search_section.layout().count()):
                widget = self.file_search_section.layout().itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
        else:
            # Collapsed - show arrow right and hide content
            self.file_search_section.setTitle(self.translations.get("file_search_section_collapsed", "▶ File Search"))
            # Hide all child widgets to free up space
            for i in range(self.file_search_section.layout().count()):
                widget = self.file_search_section.layout().itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
            # Set minimal height when collapsed
            self.file_search_section.setMaximumHeight(35)

    # =================================================================
    # DIALOGS AND EVENT HANDLERS
    # =================================================================

    def show_find_replace_dialog(self):
        """Toggle find/replace panel visibility"""
        if self.find_replace_panel.isVisible():
            self.find_replace_panel.hide_panel()
        else:
            self.find_replace_panel.show()
            self.find_replace_panel.find_edit.setFocus()

    def show_user_game_stats_list(self):
        stats_dir = os.path.join(self.steam_folder, "appcache", "stats")
        if not os.path.isdir(stats_dir):
            QMessageBox.warning(self, "Error", f"Stats directory not found:\n{stats_dir}")
            return
        stats_files = [f for f in os.listdir(stats_dir) if f.startswith("UserGameStatsSchema_") and f.endswith(".bin")]
        stats_list = []
        orig_game_id = self.game_id_edit.text()
        orig_steam_folder = self.steam_folder
        for fname in stats_files:
            m = re.match(r"UserGameStatsSchema_(\d+)\.bin", fname)
            game_id = m.group(1) if m else "?"
            file_path = os.path.join(stats_dir, fname)
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                chunks = self.binary_parser.split_chunks(file_data)
                achievement_count = sum(1 for chunk in chunks if chunk.count(b'\x01english\x00') >= 2)
            except Exception:
                achievement_count = "?"
            # Temporarily set game ID and steam folder to load version and name
            self.game_id_edit.setText(game_id)
            self.steam_folder = self.steam_folder_path.text().strip()
            
            # Read version and gamename directly from the file instead of using manual path
            version = UserGameStatsListDialog.get_version_from_file(file_path)
            gamename = UserGameStatsListDialog.get_gamename_from_file(file_path)
            
            # Check if we should use Steam API name
            if self.settings.value("UseSteamName", False, type=bool):
                m = re.search(r'UserGameStatsSchema_(\d+)\.bin$', file_path)
                if m:
                    game_id = m.group(1)
                    steam_name = self.get_steam_game_name(game_id)
                    if steam_name:
                        gamename = steam_name
            
            stats_list.append((
                gamename if gamename else self.translations.get("unknown"),
                str(version) if version else self.translations.get("unknown"),
                game_id,
                achievement_count
            ))
        # Restore original values
        self.game_id_edit.setText(orig_game_id)
        self.steam_folder = orig_steam_folder
        # Restore original UI labels
        self.version()
        self.gamename()
        # Show dialog
        dlg = UserGameStatsListDialog(self, stats_list, self.steam_game_names, self.settings)
        dlg.exec()

    def show_accent_color_picker(self):
        """Show color picker dialog for accent color selection"""
        current_custom_color = self.theme_manager.get_custom_accent_color()
        
        # If no custom color is set, use current theme default color
        initial_color = current_custom_color
        if not initial_color:
            theme_color = self.theme_manager.get_theme_default_accent_color()
            initial_color = theme_color if theme_color else QColor(52, 132, 228)  # Fallback blue
        
        color = QColorDialog.getColor(
            initial_color, 
            self, 
            self.translations.get("select_accent_color", "Select Accent Color")
        )
        
        if color.isValid():
            # Set custom accent color
            self.theme_manager.set_accent_color("custom", color)
            
            # Update menu checkmarks
            self.refresh_accent_color_menu()

    def refresh_accent_color_menu(self):
        """Refresh accent color menu checkmarks"""
        if hasattr(self, 'accent_color_actions'):
            current_mode = self.theme_manager.get_current_accent_color_mode()
            for mode, action in self.accent_color_actions.items():
                action.setChecked(mode == current_mode)

    def _on_exit_action(self):
        # Called when user selects Exit from menu
        if self.maybe_save_before_exit():
            self.close()

    def set_modified(self, value=True):
        self.modified = value

    def is_modified(self):
        return getattr(self, 'modified', False)

    def maybe_save_before_exit(self):
        if not self.is_modified():
            return True  # No changes, allow exit
        save_box = QMessageBox(self)
        save_box.setWindowTitle(self.translations.get("save_changes_title"))
        save_box.setText(self.translations.get("save_changes_msg"))
        btn_yes = save_box.addButton(self.translations.get("yes"), QMessageBox.ButtonRole.YesRole)
        btn_no = save_box.addButton(self.translations.get("no"), QMessageBox.ButtonRole.NoRole)
        btn_cancel = save_box.addButton(self.translations.get("cancel"), QMessageBox.ButtonRole.RejectRole)
        save_box.setDefaultButton(btn_yes)
        save_box.exec()
        clicked = save_box.clickedButton()

        if clicked == btn_yes:

            save_dialog = QMessageBox(self)
            save_dialog.setWindowTitle(self.translations.get("save_where_title"))
            context_lang = self.context_lang_combo.currentText()
            msg4 = self.translations.get("save_where_msg").format(context=context_lang)
            save_dialog.setText(msg4)
            btn_self = save_dialog.addButton(self.translations.get("save_for_self"), QMessageBox.ButtonRole.AcceptRole)
            btn_steam = save_dialog.addButton(self.translations.get("save_to_steam"), QMessageBox.ButtonRole.AcceptRole)
            btn_cancel2 = save_dialog.addButton(self.translations.get("cancel"), QMessageBox.ButtonRole.RejectRole)
            save_dialog.setDefaultButton(btn_self)
            save_dialog.exec()
            clicked2 = save_dialog.clickedButton()
            if clicked2 == btn_self:
                self.save_bin_know()
                self.close()
                return not self.is_modified()
            elif clicked2 == btn_steam:
                self.save_bin_unknow()
                self.close()
                return not self.is_modified()
            else:
                return False
        elif clicked == btn_no:
            return True
        else:
            return False

    def closeEvent(self, event):
        if self.maybe_save_before_exit():
            event.accept()
        else:
            event.ignore()


def main():
    global window
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    settings = QSettings("Vena", "Steam Achievement Localizer")
    language = settings.value("language", None)
    if language is None:
        language = choose_language()
        settings.setValue("language", language)
        settings.sync()
    translations = load_translations_for_language(language)

    last_version = settings.value("last_version", "")

    # Use the selected language for the warning dialog
    warning_title = translations.get("warning_title_achtung", "Achtung")
    warning_message = translations.get("warning_message", "Possible bugs, for questions please refer to the GitHub page, or write in private on Telegram: @Pan_Vena or Discord: pan_vena<br> Other my contact details can be found in 'About App'")

    if last_version != APP_VERSION:
        QMessageBox.information(
            None,
            warning_title,
            warning_message
        )
        settings.setValue("last_version", APP_VERSION)
        settings.sync()

    window = BinParserGUI(language)
    theme = settings.value("theme", "System")
    window.theme_manager.set_theme(theme)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
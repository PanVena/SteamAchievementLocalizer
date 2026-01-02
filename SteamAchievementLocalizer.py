import sys
import re
import os
import json
import time
import requests
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QTextDocument, QColor, QPalette, QPixmap, QImage
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QHBoxLayout,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QFrame, QGroupBox, QHeaderView,
    QInputDialog, QMainWindow, QColorDialog, QAbstractItemView, QProgressBar, QCheckBox
)
import certifi
import os

# Set environment variable for requests to find CA bundle in frozen apps
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from plugins import (
    HighlightDelegate, FindReplacePanel, UserGameStatsListDialog,
    ContextLangDialog, ThemeManager, BinaryParser, SteamIntegration,
    CSVHandler, FileManager, UIBuilder, HelpDialog, ContextMenuManager,
    DragDropPlugin, GameNameFetchWorker, get_available_languages_for_selection,
    get_display_name, get_code_from_display_name, AutoUpdater, IconLoader
)

if sys.platform == "win32":
    import winreg

APP_VERSION = "0.8.22" 

LOCALES_DIR = "assets/locales"
STEAM_APP_LIST_CACHE = "assets/steam.api.allgamenames.json"

def load_available_locales():
    """Load available locales from the locales directory"""
    locales = {}
    path = resource_path(LOCALES_DIR)
    if os.path.exists(path):
        for filename in os.listdir(path):
            if filename.endswith('.json'):
                file_path = os.path.join(path, filename)
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
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
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

    raise RuntimeError(f"Cannot decode JSON: {path}")

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
    
class IconWorker(QThread):
    """Worker thread for loading icons in background"""
    icon_loaded = pyqtSignal(int, int, object) # row, col, QImage

    def __init__(self, tasks, icon_loader, game_id):
        super().__init__()
        self.tasks = tasks
        self.icon_loader = icon_loader
        self.game_id = game_id
        self._is_running = True

    def run(self):
        print(f"[IconWorker] Starting with {len(self.tasks)} tasks. Game ID: {self.game_id}", flush=True)
        for row, col, icon_hash in self.tasks:
            if not self._is_running:
                break
            image = None
            try:
                # Load QImage (thread-safe)
                image = self.icon_loader.load_icon_image(icon_hash, self.game_id, size=(64, 64))
            except Exception as e:
                print(f"[IconWorker] Error loading hash {icon_hash}: {e}", flush=True)
            
            # Emit signal regardless of success to update progress
            if self._is_running:
                self.icon_loaded.emit(row, col, image)

        print("[IconWorker] Finished", flush=True)

    def stop(self):
        self._is_running = False
        self.wait()

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
        self.drag_drop_plugin = DragDropPlugin(self)
        
        # Steam game names - not loaded from file anymore, using API only
        self.steam_game_names = {}
        self.steam_app_names = self.load_steam_app_list()
        
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
        
        # Add status bar for menu tooltips
        
        # Setup status bar with progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)  # Hidden by default
        self.progress_bar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.statusBar().showMessage(self.translations.get("ready", "Ready"))
        
        # Progress tracking for batch operations
        self.progress_current = 0
        self.progress_total = 0
        

        self.settings = QSettings("Vena", "Steam Achievement Localizer")
        
        # Initialize IconLoader after settings
        self.icon_loader = IconLoader(self.settings)
        
        self.default_steam_path = self.detect_steam_path()
        
        self.force_manual_path = False
        self.manual_file_game_id = None  # Store Game ID from manually loaded file
        self.last_api_call_time = 0  # Track last Steam API call for rate limiting  


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
        self.stats_bin_path_path.setToolTip(self.translations.get("tooltip_man_select_file", ""))
        self.stats_bin_path_path.textChanged.connect(lambda text: self.settings.setValue("LastEnteredFilePath", text))
        self.stats_bin_path_btn = QPushButton(self.translations.get("man_select_file"))
        self.stats_bin_path_btn.setToolTip(self.translations.get("tooltip_man_select_file", ""))
        self.stats_bin_path_btn.clicked.connect(self.stats_bin_path_search)
        self.select_stats_bin_path_btn = QPushButton(self.translations.get("get_ach"))
        self.select_stats_bin_path_btn.setToolTip(self.translations.get("tooltip_get_ach_manual", ""))
        self.select_stats_bin_path_btn.setDefault(True)
        self.select_stats_bin_path_btn.setAutoDefault(True)
        self.select_stats_bin_path_btn.setStyleSheet("padding: 5px;")
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
        self.steam_folder_path.setToolTip(self.translations.get("tooltip_steam_folder", ""))
        self.steam_folder_path.textChanged.connect(self.on_steam_path_changed)
        self.steam_auto_path_btn = QPushButton(self.translations.get("auto"))
        self.steam_auto_path_btn.setToolTip(self.translations.get("tooltip_steam_auto", ""))
        self.steam_auto_path_btn.clicked.connect(self.steam_auto_forcing)
        self.select_steam_folder_btn = QPushButton(self.translations.get("select_steam_folder"))
        self.select_steam_folder_btn.setToolTip(self.translations.get("tooltip_select_steam_folder", ""))
        self.select_steam_folder_btn.clicked.connect(self.select_steam_folder)
        steam_folder_layout.addWidget(self.steam_folder_path)
        steam_folder_layout.addWidget(self.steam_auto_path_btn)
        steam_folder_layout.addWidget(self.select_steam_folder_btn)

        
        self.set_steam_folder_path()
      
        # --- Game ID selection ---
        game_id_layout = QHBoxLayout()
        self.game_id_edit = QLineEdit()
        self.game_id_edit.setPlaceholderText(self.translations.get("game_id_label"))
        self.game_id_edit.setToolTip(self.translations.get("tooltip_game_id", ""))
        self.game_id_edit.textChanged.connect(lambda text: self.settings.setValue("LastEnteredID", text))
        self.load_game_btn = QPushButton(self.translations.get("get_ach"))
        self.load_game_btn.setToolTip(self.translations.get("tooltip_get_ach_steam", ""))
        self.load_game_btn.setDefault(True)
        self.load_game_btn.setAutoDefault(True)
        self.load_game_btn.setStyleSheet("padding: 5px;")
        self.load_game_btn.clicked.connect(self.load_steam_game_stats)
        self.clear_game_id = QPushButton(self.translations.get("clear_and_paste"))
        self.clear_game_id.setToolTip(self.translations.get("tooltip_clear_paste", ""))
        self.clear_game_id.pressed.connect(lambda: ( 
            self.game_id_edit.clear(),
            self.game_id_edit.setText(QApplication.clipboard().text()),
            self.handle_game_id_action()
        ))
        game_id_layout.addWidget(self.game_id_edit)
        game_id_layout.addWidget(self.load_game_btn)
        game_id_layout.addWidget(self.clear_game_id)

        # --- User game stats dialog ---
        user_game_stats_layout = QHBoxLayout()
        self.user_game_stats_btn = QPushButton(self.translations.get("get_ach_UI", "Find by name"))
        self.user_game_stats_btn.setToolTip(self.translations.get("tooltip_get_ach_UI", "Choose from list, or find by game name."))
        self.user_game_stats_btn.setDefault(True)
        self.user_game_stats_btn.setAutoDefault(True)
        self.user_game_stats_btn.setStyleSheet("padding: 5px;")
        self.user_game_stats_btn.setStyleSheet("padding: 5px;")
        self.user_game_stats_btn.clicked.connect(self.show_user_game_stats_list)
        # Add Ctrl+O shortcut for opening the game list dialog
        self.user_game_stats_btn.setShortcut(QKeySequence("Ctrl+O"))
        user_game_stats_layout.addWidget(self.user_game_stats_btn)

        # --- Frame ---
        steam_group_layout = QVBoxLayout()
        steam_group_layout.addLayout(user_game_stats_layout)
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
            self.translation_lang_combo.setToolTip(self.translations.get("tooltip_translation_lang", ""))
            available_languages = get_available_languages_for_selection()
            
            # Add languages to combo box with display names
            for lang_code in available_languages:
                display_name = get_display_name(lang_code)
                self.translation_lang_combo.addItem(display_name, lang_code)
            
            # Set system language as default
                # Set first available language as default
                self.translation_lang_combo.setCurrentIndex(25)
            
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
        self.table.setToolTip(self.translations.get("tooltip_table", ""))
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.itemChanged.connect(self.on_table_item_changed)

        # --- Context Menu Manager ---
        self.context_menu_manager = ContextMenuManager(self, self.translations)
        
        # Create table actions
        self.table_actions = self.context_menu_manager.create_table_actions()
        self.undo_action = self.table_actions['undo']
        self.redo_action = self.table_actions['redo']
        self.cut_action = self.table_actions['cut']
        self.copy_action = self.table_actions['copy']
        self.paste_action = self.table_actions['paste']
        self.delete_action = self.table_actions['delete']
        self.select_all_action = self.table_actions['select_all']
        self.replace_in_column_action = self.table_actions['find_replace']
        
        # Connect select_all to table
        self.select_all_action.triggered.connect(self.table.selectAll)
        
        # Add tooltips and status bar messages
        for name, action in self.table_actions.items():
            tooltip_key = f"tooltip_{name}" if name != 'find_replace' else "tooltip_replace_in_column"
            action.setToolTip(self.translations.get(tooltip_key, ""))
            action.hovered.connect(lambda a=action: self.statusBar().showMessage(a.toolTip()))
        
        # Setup table context menu with find/replace action
        self.context_menu_manager.setup_table(self.table, [self.replace_in_column_action])
        
        # Add actions to table for keyboard shortcuts
        self.table.addAction(self.replace_in_column_action)


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

        # Setup custom context menus for all QLineEdit widgets using context menu manager
        self.context_menu_manager.setup_lineedit(self.stats_bin_path_path)
        self.context_menu_manager.setup_lineedit(self.steam_folder_path)
        self.context_menu_manager.setup_lineedit(self.game_id_edit)

        # Highlight delegate for search
        self.highlight_delegate = HighlightDelegate(self.table)
        self.table.setItemDelegate(self.highlight_delegate)

        # Add find/replace panel (hidden by default)
        self.find_replace_panel = FindReplacePanel(self, self.headers)
        self.layout.addWidget(self.find_replace_panel)
        # Initialize theme manager
        self.theme_manager = ThemeManager(self, resource_path)

        # Initialize auto-updater
        self.auto_updater = AutoUpdater(APP_VERSION, self.translations, self)
        self.auto_updater_enabled = self.settings.value("auto_update_enabled", True, type=bool)
        # Check for updates automatically on startup (if enabled in settings)
        if self.auto_updater_enabled:
            self.auto_updater.check_for_updates()

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
        # On macOS, get existing menubar or create new one
        # On other platforms, always create new
        if sys.platform == "darwin":
            # Get existing menubar if it exists
            menubar = self.menuBar()
            # Clear all existing actions/menus
            menubar.clear()

            # Initialize ui_builder with current translations
            self.ui_builder = UIBuilder(self, self.translations)
            # Populate the existing menubar
            self.ui_builder.populate_menubar(menubar)
        else:
            # On other platforms, remove old widget and create new
            old_menubar = self.menuWidget()
            if old_menubar:
                old_menubar.deleteLater()
                self.setMenuWidget(None)

            # Initialize ui_builder with current translations
            self.ui_builder = UIBuilder(self, self.translations)
            menubar = self.ui_builder.create_menubar()
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
        """Stretch columns to fill table width"""
        if self.table.columnCount() == 0:
            return
            
        header_width = self.table.viewport().width()
        total_width = header_width
        
        # Determine visible columns
        visible_columns = []
        for i in range(self.table.columnCount()):
            if not self.table.isColumnHidden(i):
                visible_columns.append(i)
        
        if not visible_columns:
            return
            
        # Calculate minimum widths
        min_widths = []
        total_min_width = 0
        
        for col in visible_columns:
            header_text = self.table.horizontalHeaderItem(col).text()
            # Special width for icon column
            if header_text == 'icon':
                # Fixed width for icon column (64px icon + padding)
                width = 80 
            else:
                # Text columns
                width = 150  # Minimum width for text columns
                
            min_widths.append(width)
            total_min_width += width
            
        # If we have extra space, distribute it
        if total_width > total_min_width:
            # Distribute extra space proportionally
            # Don't stretch icon column too much
            extra_space = total_width - total_min_width
            
            # Count flexible columns (exclude icon from major stretching)
            flexible_columns_count = 0
            for i, col in enumerate(visible_columns):
                header_text = self.table.horizontalHeaderItem(col).text()
                if header_text != 'icon':
                    flexible_columns_count += 1
            
            if flexible_columns_count > 0:
                space_per_flexible = extra_space // flexible_columns_count
                
                for i, col in enumerate(visible_columns):
                    header_text = self.table.horizontalHeaderItem(col).text()
                    if header_text == 'icon':
                        # Icon column gets only small stretch or nothing
                        self.table.setColumnWidth(col, min_widths[i])
                    else:
                        # Other columns get stretched
                        self.table.setColumnWidth(col, min_widths[i] + space_per_flexible)
            else:
                # All columns are fixed/icon? Just distribute evenly
                space_per_column = extra_space // len(visible_columns)
                for i, col in enumerate(visible_columns):
                    self.table.setColumnWidth(col, min_widths[i] + space_per_column)
        else:
            # Just use minimum widths
            for i, col in enumerate(visible_columns):
                self.table.setColumnWidth(col, min_widths[i])
        
        # Set resize mode to make sure user can still resize manually
        self.header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def resizeEvent(self, event):
        self.stretch_columns()
        super().resizeEvent(event)

    def get_row_pair_colors(self):
        """Get background colors for row pairs with guaranteed contrast"""
        palette = QApplication.instance().palette()
        bg_color_1 = palette.color(QPalette.ColorRole.Base)
        bg_color_2 = palette.color(QPalette.ColorRole.AlternateBase)
        
        # Calculate contrast
        diff = abs(bg_color_1.lightness() - bg_color_2.lightness())
        
        # If contrast is too low (unclear separation), force it
        # Increased threshold and intensity for better visibility
        if diff < 25:
            if bg_color_1.lightness() > 128:
                # Light theme -> make alternate darker (e.g. from white to light gray)
                bg_color_2 = bg_color_1.darker(112) 
            else:
                # Dark theme -> make alternate lighter (e.g. from dark gray to lighter gray)
                bg_color_2 = bg_color_1.lighter(125) 
                
        return bg_color_1, bg_color_2

    def update_row_colors(self):
        """Update row/icon background colors based on current theme palette"""
        if not hasattr(self, 'table') or self.table.rowCount() == 0:
            return
            
        bg_color_1, bg_color_2 = self.get_row_pair_colors()
                
        self.table.blockSignals(True)
        # Disable sorting temporarily
        is_sorting_enabled = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        
        try:
            for row_i in range(self.table.rowCount()):
                # Determine background color for this row pair
                pair_index = row_i // 2
                row_bg_color = bg_color_1 if pair_index % 2 == 0 else bg_color_2
                
                for col_i in range(self.table.columnCount()):
                    item = self.table.item(row_i, col_i)
                    if item:
                        item.setBackground(row_bg_color)
                    
                    # Check for cell widgets (labels for icons)
                    widget = self.table.cellWidget(row_i, col_i)
                    if widget and isinstance(widget, QLabel):
                        hex_color = row_bg_color.name()
                        widget.setStyleSheet(f"background-color: {hex_color}; border: none;")
        finally:
            self.table.setSortingEnabled(is_sorting_enabled)
            self.table.blockSignals(False)

    def changeEvent(self, event):
        """Handle theme/palette changes"""
        if event.type() == QEvent.Type.PaletteChange:
            self.update_row_colors()
        super().changeEvent(event)

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

    def get_mandatory_columns(self):
        """Get mandatory columns based on current translation language"""
        # Automatically build mapping from UI language to Steam language code from available locales
        ui_to_steam_lang = {}
        if hasattr(self, 'available_locales') and self.available_locales:
            for locale_name, locale_info in self.available_locales.items():
                steam_lang = locale_info.get('data', {}).get('_locale_info', {}).get('steam_lang_code')
                if steam_lang:
                    ui_to_steam_lang[locale_name] = steam_lang
        
        # Determine translation language
        if self.language in ui_to_steam_lang:
            translation_lang = ui_to_steam_lang[self.language]
        else:
            # For English and other UI languages, get selected language from combo box
            if hasattr(self, 'translation_lang_combo') and self.translation_lang_combo:
                translation_lang = self.translation_lang_combo.currentData()
            else:
                # Fallback to ukrainian for English UI (user can change it via combo box)
                # For other languages, use the language mapping or default to ukrainian
                translation_lang = ui_to_steam_lang.get(self.language, 'ukrainian')
        
        # Always include 'icon', 'key' and the current translation language (if available)
        mandatory = {'icon', 'key'}
        if translation_lang:
            mandatory.add(translation_lang)
        
        return mandatory
    
    def set_column_visible(self, header, visible):
        try:
            col = self.headers.index(header)
            self.table.setColumnHidden(col, not visible)
            
            # Save visible columns to QSettings
            visible_cols = self.settings.value("VisibleColumns", [])
            if visible_cols is None:
                visible_cols = []
            # Ensure it's a list
            if not isinstance(visible_cols, list):
                visible_cols = []
                
            if visible and header not in visible_cols:
                visible_cols.append(header)
            elif not visible and header in visible_cols:
                visible_cols.remove(header)
            
            self.settings.setValue("VisibleColumns", visible_cols)
            self.settings.sync()
            
            # Stretch columns after visibility change
            self.stretch_columns()
        except ValueError:
            pass
    
    def show_all_columns(self):
        """Show all columns"""
        if not hasattr(self, 'column_actions') or not self.column_actions:
            return
        
        for header, checkbox in self.column_actions.items():
            if checkbox.isEnabled():  # Skip disabled checkboxes (mandatory columns)
                checkbox.setChecked(True)
    
    def hide_all_columns(self):
        """Hide all columns except mandatory ones"""
        if not hasattr(self, 'column_actions') or not self.column_actions:
            return
        
        for header, checkbox in self.column_actions.items():
            if checkbox.isEnabled():  # Skip disabled checkboxes (mandatory columns)
                checkbox.setChecked(False)

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

                from plugins.steam_lang_codes import get_available_languages_for_selection, get_display_name
                
                self.translation_lang_label = QLabel(self.translations.get("translation_lang", "Translation:"))
                # Insert at position 0 (beginning)
                self.lang_layout.insertWidget(0, self.translation_lang_label)
                
                self.translation_lang_combo = QComboBox()
                available_languages = get_available_languages_for_selection()
                default_lang = 'ukrainian'
                
                # Add languages to combo box with display names
                for lang_code in available_languages:
                    display_name = get_display_name(lang_code)
                    self.translation_lang_combo.addItem(display_name, lang_code)
                
                # Set default language
                default_index = 0
                for i in range(self.translation_lang_combo.count()):
                    if self.translation_lang_combo.itemData(i) == default_lang:
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
        self.select_steam_folder_btn.setToolTip(self.translations.get("tooltip_select_steam_folder", ""))
        self.steam_auto_path_btn.setText(self.translations.get("auto"))
        self.steam_auto_path_btn.setToolTip(self.translations.get("tooltip_steam_auto", ""))
        self.game_id_edit.setPlaceholderText(self.translations.get("game_id_label"))
        self.game_id_edit.setToolTip(self.translations.get("tooltip_game_id", ""))
        self.load_game_btn.setText(self.translations.get("get_ach"))
        self.load_game_btn.setToolTip(self.translations.get("tooltip_get_ach_steam", ""))
        self.clear_game_id.setText(self.translations.get("clear_and_paste"))
        self.clear_game_id.setToolTip(self.translations.get("tooltip_clear_paste", ""))
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
        
        if isinstance(self.countby2, int):
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

        if update_menubar:
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

    def show_help_dialog(self):
        """Show the help dialog"""
        dialog = HelpDialog(self, self.translations)
        dialog.exec()

    def check_for_updates_manual(self):
        """Manually check for updates (triggered from Help menu)"""
        self.auto_updater.check_for_updates(manual=True)

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
        # Trigger saving if needed
        if not self.check_unsaved_changes():
            return
        
        # Reset force_manual_path to ensure we use Steam path when loading by game ID
        self.force_manual_path = False
        self.manual_file_game_id = None
            
        # Get game ID and steam path
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

    def parse_and_fill_table(self, show_success_msg=True):
        # Check if we have data to parse
        if not hasattr(self, 'raw_data') or not self.raw_data:
            return
        
        # Load visible columns from QSettings
        visible_columns = self.settings.value("VisibleColumns", [])
        
        # Migration: if VisibleColumns is empty but HiddenColumns exists, migrate
        if not visible_columns:
            hidden_columns = self.settings.value("HiddenColumns", [])
            if hidden_columns and isinstance(hidden_columns, list):
                # If we have old hidden columns setting, we need to migrate
                # We'll handle this after we know what columns exist
                pass
            visible_columns = []
        
        if visible_columns is None:
            visible_columns = []
        # Ensure it's a list and convert to set for faster lookup
        if not isinstance(visible_columns, list):
            visible_columns = []
        visible_columns_set = set(visible_columns)
        
        # Use binary parser plugin
        all_rows, headers = self.binary_parser.parse_binary_data(self.raw_data)
        self.chunks = self.binary_parser.chunks
        self.headers = self.prioritize_headers(headers)  # Prioritize headers
        
        # Check if icons should be loaded
        load_icons = self.settings.value("LoadIcons", True, type=bool)
        if not load_icons and 'icon' in self.headers:
            self.headers.remove('icon')
        
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
        
        # Get current game ID for icon URLs
        game_id = self.current_game_id() if hasattr(self, 'current_game_id') else None
        
        # Colors for alternating row pairs (zebra striping for achievements)
        bg_color_1, bg_color_2 = self.get_row_pair_colors()
        
        # Prepare for icon loading
        icon_tasks = []
        placeholder = None
        self.icons_to_load_total = 0
        self.icons_loaded_count = 0
        
        if 'icon' in self.headers:
            placeholder = self.icon_loader.get_placeholder_icon(size=(64, 64))
            self.icons_to_load_total = sum(1 for row in self.data_rows if row.get('icon', ''))
            
        # Show progress bar for icons
        if self.icons_to_load_total > 0:
            self.show_progress(self.translations.get("loading", "Loading icons..."), total=self.icons_to_load_total)
            
        icon_rows_to_merge = []

        # Stop existing worker if any
        if hasattr(self, 'icon_worker') and self.icon_worker is not None:
             self.icon_worker.stop()
             self.icon_worker = None
        
        for row_i, row in enumerate(self.data_rows):
            # Determine background color for this row pair
            pair_index = row_i // 2
            row_bg_color = bg_color_1 if pair_index % 2 == 0 else bg_color_2
            
            for col_i, col_name in enumerate(self.headers):
                value = row.get(col_name, '')

                # Special handling for icon column
                if col_name == 'icon' and value:
                    # Check if this is a key row (not _opis)
                    key_value = row.get('key', '')
                    is_main_row = not key_value.endswith('_opis')
                    
                    if is_main_row:
                        # This is the main achievement row, create icon label
                        icon_label = QLabel()
                        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # Set background
                        hex_color = row_bg_color.name()
                        icon_label.setStyleSheet(f"background-color: {hex_color}; border: none;")
                        
                        # Set placeholder initially
                        if placeholder:
                            icon_label.setPixmap(placeholder)
                        
                        # Add to task list for background loading
                        icon_tasks.append((row_i, col_i, value))
                        
                        # Set widget in cell
                        self.table.setCellWidget(row_i, col_i, icon_label)
                        
                        # Also set an empty item so cell is selectable
                        item = QTableWidgetItem('')
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setBackground(row_bg_color) # Set background
                        self.table.setItem(row_i, col_i, item)
                        
                        # Mark this row for merging if next row is _opis
                        if row_i + 1 < len(self.data_rows):
                            next_key = self.data_rows[row_i + 1].get('key', '')
                            if next_key == f"{key_value}_opis":
                                icon_rows_to_merge.append(row_i)
                    else:
                        # This is _opis row, just set empty item (will be merged)
                        item = QTableWidgetItem('')
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setBackground(row_bg_color) # Set background
                        self.table.setItem(row_i, col_i, item)
                else:
                    # Normal text item
                    item = QTableWidgetItem(value)
                    item.setBackground(row_bg_color) # Set background
                    
                    if col_name == 'key':
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.table.setItem(row_i, col_i, item)
        
        # Merge icon cells for key and key_opis rows
        if 'icon' in self.headers:
            icon_col = self.headers.index('icon')
            for row_i in icon_rows_to_merge:
                # Merge current row with next row (key + key_opis)
                self.table.setSpan(row_i, icon_col, 2, 1)

        # Start icon worker if tasks exist
        if icon_tasks:
            self.icon_worker = IconWorker(icon_tasks, self.icon_loader, str(game_id) if game_id else None)
            self.icon_worker.icon_loaded.connect(self.update_icon_cell)
            self.icon_worker.finished.connect(self.hide_progress)
            self.icon_worker.start()
            

        
        self.table.blockSignals(False)
        
        # Глобальний режим видимості колонок (мов)
        mandatory_columns = self.get_mandatory_columns()  # Always visible

        # Глобальний список видимих колонок (мов)
        visible_columns = self.settings.value("VisibleColumns", None)
        if visible_columns is None or not isinstance(visible_columns, list) or not visible_columns:
            # Якщо користувач не налаштовував — показувати всі доступні
            visible_columns_set = set(self.headers)
        else:
            visible_columns_set = set(visible_columns)

        # Оновити глобальний список, якщо з'явилися нові колонки (наприклад, після відкриття іншої гри)
        # Додаємо тільки якщо користувач ще не налаштовував (тобто якщо visible_columns був None або порожній)
        if visible_columns is None or not isinstance(visible_columns, list) or not visible_columns:
            self.settings.setValue("VisibleColumns", list(self.headers))
            self.settings.sync()

        for i, header in enumerate(self.headers):
            if header in mandatory_columns:
                self.table.setColumnHidden(i, False)
            elif header not in visible_columns_set:
                self.table.setColumnHidden(i, True)
            else:
                self.table.setColumnHidden(i, False)
                
        # Stretch columns initially to fill width
        self.stretch_columns()
        self.update_row_heights()
        self.create_menubar()
        self.version()
        self.gamename()
        self.countby2 = self.binary_parser.get_achievement_count(self.raw_data)
        self.ach_number.setText(f"{self.translations.get('ach_number')}{self.countby2}")

        # Collapse file search section after loading table
        if hasattr(self, 'file_search_section'):
            self.file_search_section.setChecked(False)

        if show_success_msg:
            msg = self.translations.get("records_loaded").format(count=len(all_rows), countby2=self.countby2)
            QMessageBox.information(self, self.translations.get("success"), msg)

    def _setup_icon_worker(self, icon_tasks):
        """Helper to stop existing worker and start a new one if needed"""
        if hasattr(self, 'icon_worker') and self.icon_worker is not None:
             self.icon_worker.stop()
             self.icon_worker = None
        
        if icon_tasks:
            game_id = self.current_game_id() if hasattr(self, 'current_game_id') else None
            self.icon_worker = IconWorker(icon_tasks, self.icon_loader, str(game_id) if game_id else None)
            self.icon_worker.icon_loaded.connect(self.update_icon_cell)
            self.icon_worker.finished.connect(self.hide_progress)
            self.icon_worker.start()

    def on_load_icons_toggled(self, checked):
        """Handle toggling of icon loading option"""
        self.settings.setValue("LoadIcons", checked)
        self.settings.sync()
        
        # If we have data loaded, reload the table to apply changes
        if hasattr(self, 'raw_data') and self.raw_data:
             self.parse_and_fill_table(show_success_msg=False)

    def update_icon_cell(self, row, col, image):
        """Slot to update icon cell when loaded from background thread"""
        if row < self.table.rowCount() and col < self.table.columnCount():
            if image and not image.isNull():
                widget = self.table.cellWidget(row, col)
                if isinstance(widget, QLabel):
                    pixmap = QPixmap.fromImage(image)
                    widget.setPixmap(pixmap)
        
        # Update progress bar
        if self.icons_to_load_total > 0:
            self.update_progress(increment=1, message=self.translations.get("loading_icons", "Loading icons"))
            
            # Hide when done
            if self.icons_loaded_count >= self.icons_to_load_total:
                self.hide_progress()

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
            
            # Add Restart Steam button
            restart_btn = msg_box.addButton(self.translations.get("restart_steam"), QMessageBox.ButtonRole.ActionRole)
            ok_button = msg_box.addButton(self.translations.get("button_ok"), QMessageBox.ButtonRole.AcceptRole)
            
            msg_box.exec()
            
            if msg_box.clickedButton() == restart_btn:
                self.restart_steam(confirm=False)
            
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
        if not self.check_unsaved_changes():
             return

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

        # Try to extract game_id from filename and store it separately
        # Don't overwrite the user's Game ID field
        import re
        m = re.search(r'UserGameStatsSchema_(\d+)\.bin$', path)
        if m:
            self.manual_file_game_id = m.group(1)
        else:
            self.manual_file_game_id = None

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
        ).format(gamename=self.gamename())
        
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

    def _get_default_export_name(self, suffix=""):
        game_name = self.gamename()
        # Check against None or the localized "Unknown" string
        if not game_name or game_name == self.translations.get("unknown", "Unknown"):
            return f"export{suffix}.csv"
        
        # Sanitize filename: keep alphanumerics, spaces, dashes, underscores
        safe_name = "".join([c for c in game_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
        if not safe_name:
            return f"export{suffix}.csv"
            
        return f"{safe_name}{suffix}.csv"

    def export_csv_all(self):
        """Export all data to CSV using csv_handler plugin"""
        default_name = self._get_default_export_name()
        fname, _ = QFileDialog.getSaveFileName(self, self.translations.get("export_csv_all_file_dialog"), default_name, 'CSV Files (*.csv)')
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

        default_name = self._get_default_export_name("_all_table")
        fname, _ = QFileDialog.getSaveFileName(self,self.translations.get("export_csv_all_file_dialog"), default_name, "CSV Files (*.csv)")
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
                # Skip hidden columns
                if self.table.isColumnHidden(col_i):
                    continue

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
                # Skip hidden columns to avoid calculation issues
                if self.table.isColumnHidden(col):
                    continue
                    
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
        - icon (if exists) > key > translation language > english > others
        The translation column will use existing data if available.
        """
        # Separate icon and key from other headers
        has_icon = 'icon' in headers
        headers = [h for h in headers if h not in ['icon', 'key']]
        
        # Start with icon (if exists) and key
        if has_icon:
            prioritized = ['icon', 'key']
        else:
            prioritized = ['key']
        
        # Determine translation language based on UI or user selection
        # Automatically build mapping from UI language to Steam language code from available locales
        ui_to_steam_lang = {}
        if hasattr(self, 'available_locales') and self.available_locales:
            for locale_name, locale_info in self.available_locales.items():
                steam_lang = locale_info.get('data', {}).get('_locale_info', {}).get('steam_lang_code')
                if steam_lang:
                    ui_to_steam_lang[locale_name] = steam_lang
        
        if self.language in ui_to_steam_lang:
            translation_lang = ui_to_steam_lang[self.language]
        else:
            # For English and other UI languages, get selected language from combo box
            if hasattr(self, 'translation_lang_combo') and self.translation_lang_combo:
                translation_lang = self.translation_lang_combo.currentData()
            else:
                # Fallback to ukrainian for English UI (user can change it via combo box)
                # For other languages, use the language mapping or default to ukrainian
                translation_lang = ui_to_steam_lang.get(self.language, 'ukrainian')
        
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
    
    def save_column_widths(self):
        """Save current column widths"""
        self.column_widths = {}
        for i in range(self.table.columnCount()):
            self.column_widths[i] = self.table.columnWidth(i)

    def restore_column_widths(self):
        """Restore saved column widths"""
        if hasattr(self, 'column_widths'):
            for i, width in self.column_widths.items():
                if i < self.table.columnCount():
                    self.table.setColumnWidth(i, width)

    def refresh_table(self):
        """Update table content from data structure without recreating everything"""
        self.save_column_widths()
        self.table.blockSignals(True)
        
        # Colors for alternating row pairs
        bg_color_1, bg_color_2 = self.get_row_pair_colors()
        
        # Prepare for icon loading
        icon_tasks = []
        placeholder = None
        self.icons_to_load_total = 0
        self.icons_loaded_count = 0
        
        if 'icon' in self.headers:
             placeholder = self.icon_loader.get_placeholder_icon(size=(64, 64))
             self.icons_to_load_total = sum(1 for row in self.data_rows if row.get('icon', ''))
        
        # Show progress bar for icons
        if self.icons_to_load_total > 0:
            self.show_progress(self.translations.get("loading", "Loading icons..."), total=self.icons_to_load_total)
            
        for row_i, row in enumerate(self.data_rows):
            # Determine background color for this row pair
            pair_index = row_i // 2
            row_bg_color = bg_color_1 if pair_index % 2 == 0 else bg_color_2
            
            for col_i, col_name in enumerate(self.headers):
                value = row.get(col_name, '')
                
                # Special handling for icon column
                if col_name == 'icon' and value:
                    # Check if this is a key row (not _opis)
                    key_value = row.get('key', '')
                    is_main_row = not key_value.endswith('_opis')
                    
                    if is_main_row:
                        icon_label = QLabel()
                        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        hex_color = row_bg_color.name()
                        icon_label.setStyleSheet(f"background-color: {hex_color}; border: none;")
                        
                        if placeholder:
                            icon_label.setPixmap(placeholder)
                        
                        icon_tasks.append((row_i, col_i, value))
                        self.table.setCellWidget(row_i, col_i, icon_label)
                        
                        # Set empty text item so cell is selectable but doesn't show hash
                        item = QTableWidgetItem('')
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setBackground(row_bg_color)
                        self.table.setItem(row_i, col_i, item)
                        continue

                # Standard text item
                if self.table.item(row_i, col_i):
                    self.table.item(row_i, col_i).setText(value)
                    self.table.item(row_i, col_i).setBackground(row_bg_color)
                else:
                    item = QTableWidgetItem(value)
                    if col_name == 'key':
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setBackground(row_bg_color)
                    self.table.setItem(row_i, col_i, item)
        
        self._setup_icon_worker(icon_tasks)
        
        self.table.blockSignals(False)
        self.restore_column_widths()

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
        """Recreate table with new headers (used when changing language, so data doesn't change but headers do)"""
        # Save current widths before resetting
        self.save_column_widths()
        
        self.table.clear()
        self.table.setColumnCount(len(self.headers))
        
        # Updated header labels
        header_labels = []
        for header in self.headers:
            if header == 'key':
                header_labels.append(header.upper())
            else:
                display_name = get_display_name(header)
                if '(' in display_name:
                    display_name = display_name.replace(' (', '\\n(')
                header_labels.append(display_name)
                
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.setRowCount(len(self.data_rows))
        
        # Colors for alternating row pairs
        bg_color_1, bg_color_2 = self.get_row_pair_colors()
        
        # Prepare for icon loading
        icon_tasks = []
        placeholder = None
        self.icons_to_load_total = 0
        self.icons_loaded_count = 0
        
        if 'icon' in self.headers:
             placeholder = self.icon_loader.get_placeholder_icon(size=(64, 64))
             self.icons_to_load_total = sum(1 for row in self.data_rows if row.get('icon', ''))
             
        # Show progress bar for icons
        if self.icons_to_load_total > 0:
            self.show_progress(self.translations.get("loading", "Loading icons..."), total=self.icons_to_load_total)
            
        self.table.blockSignals(True)
        for row_i, row in enumerate(self.data_rows):
            # Determine background color for this row pair
            pair_index = row_i // 2
            row_bg_color = bg_color_1 if pair_index % 2 == 0 else bg_color_2
            
            for col_i, col_name in enumerate(self.headers):
                value = row.get(col_name, '')
                
                # Special handling for icon column
                if col_name == 'icon' and value:
                    key_value = row.get('key', '')
                    is_main_row = not key_value.endswith('_opis')
                    
                    if is_main_row:
                        icon_label = QLabel()
                        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        hex_color = row_bg_color.name()
                        icon_label.setStyleSheet(f"background-color: {hex_color}; border: none;")
                        
                        if placeholder:
                            icon_label.setPixmap(placeholder)
                        
                        icon_tasks.append((row_i, col_i, value))
                        self.table.setCellWidget(row_i, col_i, icon_label)
                        
                        item = QTableWidgetItem('')
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setBackground(row_bg_color)
                        self.table.setItem(row_i, col_i, item)
                        continue

                item = QTableWidgetItem(value)
                if col_name == 'key':
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                item.setBackground(row_bg_color)
                self.table.setItem(row_i, col_i, item)
        
        self._setup_icon_worker(icon_tasks)
        
        self.table.blockSignals(False)
        self.restore_column_widths()

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
        # Use already loaded data instead of re-reading file
        if not hasattr(self, 'raw_data') or not self.raw_data:
            if hasattr(self, "version_label"):
                self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
            return None

        # Use binary parser plugin
        version_number = self.binary_parser.get_version(self.raw_data)

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
    
    def show_progress(self, message=None, total=1):
        """Show progress bar in status bar for batch operations"""
        if message is None:
            message = self.translations.get("loading", "Loading...")
        self.progress_current = 0
        self.progress_total = total
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"{message} 0/{total}")
        self.progress_bar.setVisible(True)
        QApplication.processEvents()
    
    def update_progress(self, increment=1, message=None):
        """Update progress bar - increment by 1 and show X/Y format"""
        if message is None:
            message = self.translations.get("loading", "Loading")
        self.progress_current += increment
        self.progress_bar.setValue(self.progress_current)
        self.progress_bar.setFormat(f"{message} {self.progress_current}/{self.progress_total}")
        QApplication.processEvents()
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
        self.progress_current = 0
        self.progress_total = 0
        self.statusBar().showMessage(self.translations.get("ready", "Ready"))
        QApplication.processEvents()

    def load_steam_app_list(self):
        """Load Steam app list from local cache"""
        cache_path = resource_path(STEAM_APP_LIST_CACHE)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert list to dict for O(1) lookup: {appid: name}
                    return {str(app['appid']): app['name'] for app in data.get('applist', {}).get('apps', [])}
            except Exception:
                pass
        return {}

    def fetch_game_name_from_api(self, appid, progress_callback=None, is_cancelled=None):
        """Fetch game name from Steam Store API with error handling"""
        try:
            if progress_callback:
                progress_callback(0, f"Fetching game {appid}...")
            
            # Check if operation was cancelled
            if is_cancelled and is_cancelled():
                return None
            
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            response = requests.get(url, timeout=10, verify=True)
            response.raise_for_status()
            data = response.json()
            
            if progress_callback:
                progress_callback(100, f"Loaded game {appid}")
                
            if str(appid) in data and data[str(appid)]['success']:
                return data[str(appid)]['data']['name']
            else:
                # Game exists but API returned success=false (delisted, region-locked, etc.)
                print(f"[API] Game {appid}: API returned success=false")
                return "API_FAILED"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"[API] Game {appid}: Rate limited (429)")
                return "RATE_LIMITED"
            else:
                print(f"[API] Game {appid}: HTTP error {e.response.status_code}")
                return "API_ERROR"
        except requests.exceptions.Timeout:
            print(f"[API] Game {appid}: Request timeout")
            return "TIMEOUT"
        except requests.exceptions.RequestException as e:
            print(f"[API] Game {appid}: Network error - {str(e)}")
            return "NETWORK_ERROR"
        except Exception as e:
            print(f"[API] Game {appid}: Unexpected error - {str(e)}")
            return "UNKNOWN_ERROR"
    
    def save_game_name_to_cache(self, appid, name):
        """Save game name to QSettings cache"""
        cache_key = f"GameNameCache/{appid}"
        self.settings.setValue(cache_key, name)
        self.settings.sync()
    
    def get_game_name_from_cache(self, appid):
        """Get game name from QSettings cache"""
        cache_key = f"GameNameCache/{appid}"
        return self.settings.value(cache_key, None)
    
    def get_steam_game_name(self, appid, show_progress=True):
        """
        Get game name using offline-first approach.
        
        Priority order (offline-first):
        1. QSettings cache (fastest, most recent)
        2. Local JSON file (steam.api.allgamenames.json - works offline)
        3. Steam API (requires internet, only for games not in JSON)
        
        This ensures the app works offline for games in the JSON database,
        and only fetches from the internet for truly unknown games.
        
        Args:
            appid: Steam App ID
            show_progress: Whether to show progress bar
        """
        if not appid:
            return None
        
        appid_str = str(appid)
        
        # 1. Check QSettings cache first (most specific/recent)
        cached_name = self.get_game_name_from_cache(appid_str)
        if cached_name:
            # Don't return error codes from cache, treat them as not cached
            if cached_name not in ["RATE_LIMITED", "API_FAILED", "API_ERROR", "TIMEOUT", "NETWORK_ERROR", "UNKNOWN_ERROR"]:
                return cached_name
            
        # 2. Check local full app list (bulk cache from JSON - works offline)
        if hasattr(self, 'steam_app_names') and appid_str in self.steam_app_names:
            name = self.steam_app_names[appid_str]
            # Save to QSettings cache for faster future access
            self.save_game_name_to_cache(appid_str, name)
            return name
        
        # 3. Fetch from Steam API (individual request for new/missing games - requires internet)
        if show_progress:
            self.show_progress(self.translations.get("loading", "Loading"), total=1)
        
        try:
            api_result = self.fetch_game_name_from_api(appid)
            if api_result and not api_result.startswith("RATE_LIMITED") and not api_result.startswith("API_") and not api_result.endswith("_ERROR"):
                # Success - got a real game name
                self.save_game_name_to_cache(appid, api_result)
                self.settings.sync()
                if show_progress:
                    self.update_progress(increment=1, message="Loading")
                return api_result
            elif api_result in ["RATE_LIMITED", "API_FAILED", "API_ERROR", "TIMEOUT", "NETWORK_ERROR", "UNKNOWN_ERROR"]:
                # Error occurred - cache the error to avoid retrying immediately
                # But don't save permanently, so next app restart can try again
                if show_progress:
                    self.update_progress(increment=1, message="Error")
                return None
            else:
                # API returned None or empty
                if show_progress:
                    self.update_progress(increment=1, message="Not found")
                return None
        finally:
            if show_progress:
                self.hide_progress()
        
        return None

    def get_game_name_for_id(self, appid, raw_data=None, show_progress=False):
        """
        Get game name using game ID only (cache-first approach).
        
        Lookup order:
        1. Session memory cache
        2. QSettings cache
        3. JSON file (steam_app_names)
        4. Binary file (marked with * as code name)
        5. Return "Unknown"
        
        Never makes API calls automatically.
        
        Args:
            appid: Steam App ID
            raw_data: Binary file data (optional, for fallback)
            show_progress: Ignored (kept for compatibility)
        """
        if not appid:
            return self.translations.get("unknown", "Unknown")
            
        appid_str = str(appid)
        
        # 1. Check session memory cache
        if appid_str in self.steam_game_names:
            return self.steam_game_names[appid_str]
        
        # 2. Check QSettings cache
        cached = self.get_game_name_from_cache(appid_str)
        if cached:
            self.steam_game_names[appid_str] = cached
            return cached
        
        # 3. Check JSON file
        if appid_str in self.steam_app_names:
            name = self.steam_app_names[appid_str]
            self.steam_game_names[appid_str] = name
            self.save_game_name_to_cache(appid_str, name)
            return name
        
        # 4. Fallback to binary file (mark as code name with *)
        if raw_data:
            binary_name = self.binary_parser.get_gamename(raw_data)
            if binary_name and binary_name != self.translations.get("unknown", "Unknown"):
                # Mark as code name from binary
                marked_name = f"*{binary_name}"
                self.steam_game_names[appid_str] = marked_name
                # Don't save to QSettings cache - we want to try API next time
                return marked_name
        
        # 5. Return unknown
        unknown = self.translations.get("unknown", "Unknown")
        self.steam_game_names[appid_str] = unknown
        return unknown
    
    

    
    def gamename(self):
        # Use already loaded data instead of re-reading file
        if not hasattr(self, 'raw_data') or not self.raw_data:
            if hasattr(self, "gamename_label"):
                self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
            self.update_window_title()
            return None

        game_id = self.current_game_id()
        name = self.get_game_name_for_id(game_id, raw_data=self.raw_data)

        if hasattr(self, "gamename_label"):
            self.gamename_label.setText(f"{self.translations.get('gamename')}{name}")

        self.update_window_title(name)
        return name

    def update_window_title(self, game_name=None):
        """Update window title with app name, version and optional game name"""
        title = f"{self.translations.get('app_title')}{APP_VERSION}"
        if game_name:
             # Use a separator, e.g., " - Game Name"
             title += f" - {game_name}"
        self.setWindowTitle(title)

    def current_game_id(self):
        # Return game ID based on current mode (manual or steam path)
        if self.force_manual_path:
            # Use the stored manual file game ID if available
            if hasattr(self, 'manual_file_game_id') and self.manual_file_game_id:
                return self.manual_file_game_id
            # Fallback: extract from filename
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
        
        if not stats_files:
            QMessageBox.information(self, self.translations.get("info"), self.translations.get("no_stats_files", "No stats files found."))
            return

        # Show progress bar
        self.show_progress(total=len(stats_files))
        
        # Create and start worker
        self.worker = GameNameFetchWorker(stats_files, stats_dir, self)
        self.worker.progress.connect(lambda current, total, msg: self.update_progress(message=msg))
        self.worker.api_error.connect(self.on_api_error)
        self.worker.finished.connect(self.on_stats_loading_finished)
        self.worker.start()

    def on_api_error(self, error_type):
        """Handle Steam API errors (blocks/rate limits)"""
        if error_type in ["RATE_LIMITED", "TOO_MANY_FAILURES"]:
            # Store instance to prevent garbage collection for non-modal dialog
            self.api_error_dialog = QMessageBox(self)
            self.api_error_dialog.setIcon(QMessageBox.Icon.Warning)
            self.api_error_dialog.setWindowTitle(self.translations.get("api_block_warning_title", "Steam API Block Detected"))
            self.api_error_dialog.setText(self.translations.get("api_block_warning_message", "Steam API seems to be blocking requests..."))
            self.api_error_dialog.setWindowFlags(self.api_error_dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.api_error_dialog.show()

    def on_stats_loading_finished(self, stats_list):
        self.hide_progress()
        
        # Mark fetch as completed if UseSteamName is ON
        if self.settings.value("UseSteamName", False, type=bool):
            self.settings.setValue("SteamNamesFetchCompleted", True)
            self.settings.sync()
        
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

    def check_unsaved_changes(self):
        """
        Checks for unsaved changes and prompts user to save if necessary.
        Returns True if it's safe to proceed (changes saved or discarded, or no changes).
        Returns False if user cancelled.
        """
        if not self.is_modified():
            return True  # No changes, safe to proceed

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
            
            # Helper to safely get current text or fallback
            context_lang = 'English'
            if hasattr(self, 'translation_lang_combo') and self.translation_lang_combo:
                 context_lang = self.translation_lang_combo.currentText()
            
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
                return not self.is_modified()
            elif clicked2 == btn_steam:
                self.save_bin_unknow()
                return not self.is_modified()
            else:
                return False # User cancelled second dialog
        elif clicked == btn_no:
            return True # User explicitly said No, so proceed without saving
        else:
            return False # User cancelled first dialog

    def maybe_save_before_exit(self):
        if self.check_unsaved_changes():
             # If check passed (saved or discarded), we can close
             return True
        return False

    def closeEvent(self, event):
        if hasattr(self, 'icon_worker') and self.icon_worker:
            self.icon_worker.stop()
        if self.maybe_save_before_exit():
            event.accept()
        else:
            event.ignore()

    def restart_steam(self, confirm=True):
        """
        Restart Steam client.
        :param confirm: If True, asks for confirmation before restarting.
        """
        if confirm:
            # Ask for confirmation first
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle(self.translations.get("q_restart_steam"))
            msg_box.setText(self.translations.get("msg_restart_steam"))
            yes_button = msg_box.addButton(self.translations.get("button_yes"), QMessageBox.ButtonRole.YesRole)
            no_button = msg_box.addButton(self.translations.get("button_no"), QMessageBox.ButtonRole.NoRole)
            msg_box.exec()
            
            if msg_box.clickedButton() != yes_button:
                return

        if self.steam_integration.restart_steam():
            # Close app if successful restart initiated?
            # Or just let it be. Steam restart will kill Steam, but this app is independent.
            # Maybe show a fast message "Restarting..."
            self.statusBar().showMessage("Restarting Steam...", 5000)
        else:
            QMessageBox.warning(self, self.translations.get("error"), "Failed to restart Steam")

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
        # Create custom message box with checkbox
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(warning_title)
        msg_box.setText(warning_message)
        
        # Add checkbox for icon loading
        cb = QCheckBox(translations.get("load_icons_option", "Load achievement icons"))
        cb.setChecked(settings.value("LoadIcons", True, type=bool))
        msg_box.setCheckBox(cb)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
        # Save settings
        settings.setValue("LoadIcons", cb.isChecked())
        settings.setValue("last_version", APP_VERSION)
        settings.sync()

    window = BinParserGUI(language)
    theme = settings.value("theme", "System")
    window.theme_manager.set_theme(theme)
    window.show()



    sys.exit(app.exec())


if __name__ == "__main__":
    main()
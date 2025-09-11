import sys
import csv
import re
import os
import subprocess
import json
import shutil
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon, QAction,QKeySequence, QTextDocument
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QHBoxLayout,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QFrame, QGroupBox, QHeaderView,
    QInputDialog, QMenu, QMenuBar, QWidgetAction, QCheckBox, QMainWindow
)
from assets.plugins.highlight_delegate import HighlightDelegate
from assets.plugins.find_replace_dialog import FindReplaceDialog
from assets.plugins.user_game_stats_list_dialog import UserGameStatsListDialog
from assets.plugins.context_lang_dialog import ContextLangDialog

if sys.platform == "win32":
    import winreg

APP_VERSION = "7.7.9" 

EXCLUDE_WORDS = {b'max', b'maxchange', b'min', b'token', b'name', b'icon', b'hidden', b'icon_gray', b'Hidden',b'', b'russian',b'Default',b'gamename',b'id',b'incrementonly',b'max_val',b'min_val',b'operand1',b'operation',b'type',b'version'}

LANG_FILES = {
    "English": "assets/locales/lang_en.json",
    "Українська": "assets/locales/lang_ua.json",
    "Polski": "assets/locales/lang_pl.json"
}


def choose_language():
    settings = QSettings("Vena", "Steam Achievement Localizer")
    current_language = settings.value("language", None)

    if current_language:
        return current_language  # already saved language

    # Ask user to choose language
    lang, ok = QInputDialog.getItem(
        None,
        "Select Language",
        "Choose your language:",
        list(LANG_FILES.keys()),
        0,
        False
    )
    if ok and lang:
        settings.setValue("language", lang)
        return lang

    return "English"  # default language

def split_chunks(data: bytes):
    pattern = re.compile(b'\x00bits\x00|\x02bit\x00')
    positions = [m.start() for m in pattern.finditer(data)]
    chunks = []
    for i in range(len(positions)):
        start = positions[i]
        end = positions[i + 1] if i + 1 < len(positions) else len(data)
        chunks.append(data[start:end])
    return chunks


def extract_key_and_data(chunk: bytes):
    key_pattern = re.compile(b'\x00\x01name\x00(.*?)\x00', re.DOTALL)
    key_match = key_pattern.search(chunk)
    if not key_match:
        return None

    # Skip any chunks without an english field.
    if b'\x01english\x00' not in chunk:
        return None

    return key_match.group(1).decode(errors='ignore')

def extract_words(chunk: bytes):
    pattern = re.compile(b'\x01(.*?)\x00', re.DOTALL)
    matches = pattern.findall(chunk)
    words = []
    for w in matches:
        if w in EXCLUDE_WORDS:
            continue
        words.append(w.decode(errors='ignore'))
    return words
def extract_values(chunk: bytes, words: list):
    values = []
    pos = 0
    for word in words:
        search_pattern = b'\x01' + word.encode() + b'\x00'
        idx = chunk.find(search_pattern, pos)
        if idx == -1:
            values.append('')
            continue
        idx += len(search_pattern)
        end_idx = chunk.find(b'\x00', idx)
        if end_idx == -1:
            values.append('')
            pos = idx
            continue
        val = chunk[idx:end_idx].decode(errors='ignore')
        values.append(val)
        pos = end_idx + 1
    return values
    
def resource_path(relative_path: str) -> str:
    """Returns the correct path to resources for both .py and .exe (Nuitka/PyInstaller)"""
    if getattr(sys, 'frozen', False):
        # when we are runnimg as a bundled exe
        base_path = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(sys.executable)
    else:
        # when we are running as a normal .py file
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
    translations = load_json_with_fallback(resource_path(LANG_FILES.get(language, LANG_FILES["English"])))
    raise RuntimeError(f"{translations.get('cannot_decode_json')}{path}")
    
class BinParserGUI(QMainWindow):

    def __init__(self, language="English"):
        self.modified = False
        super().__init__(parent=None)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.language = language
        self.translations = self.load_language(language)
        self.setWindowTitle(f"{self.translations.get('app_title')}{APP_VERSION}")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        self.setMinimumSize(800, 800)
        self.set_window_size()

        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)
        

        self.settings = QSettings("Vena", "Steam Achievement Localizer")
        self.default_steam_path = self.detect_steam_path()
        
        
        
        self.force_manual_path = False  


        
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
        self.layout.addWidget(self.stats_group)   
        
        
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
        self.layout.addWidget(box_1)


        # --- Steam folder selection ---
        steam_folder_layout = QHBoxLayout()
        self.steam_folder_path = QLineEdit()
        self.steam_folder_path.setPlaceholderText(self.translations.get("steam_folder_label"))
        self.steam_folder_path.textChanged.connect(self.on_steam_path_changed)
        self.select_steam_folder_btn = QPushButton(self.translations.get("select_steam_folder"))
        self.select_steam_folder_btn.clicked.connect(self.select_steam_folder)
        steam_folder_layout.addWidget(self.steam_folder_path)
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
        self.layout.addWidget(self.steam_group)
        

       
        
        # --- Language selection and info ---
        lang_layout = QHBoxLayout()

        # 2. Game name
        self.gamename_label = QLabel(
            f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
        lang_layout.addWidget(self.gamename_label)

        # Vertical separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.VLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        lang_layout.addWidget(line2)

        # 3. File version
        self.version_label = QLabel(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
        lang_layout.addWidget(self.version_label)



        # --- Frame ---
        box = QGroupBox("")  
        box.setFlat(False)
        box.setLayout(lang_layout)
        self.layout.addWidget(box)


        
        # -- Undo/Redo ---
        self.undo_stack = []
        self.redo_stack = []
        self.is_undoing = False
        self.is_redoing = False
        

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
        self.replace_in_column_action = QAction(self.translations.get("replace_in_column", "Replace"), self)
        self.replace_in_column_action.triggered.connect(self.show_find_replace_dialog)
        self.table.addAction(self.replace_in_column_action)

        # Highlight delegate for search
        self.highlight_delegate = HighlightDelegate(self.table)
        self.table.setItemDelegate(self.highlight_delegate)

        # Create menubar
        self.create_menubar()
      
    
            
    def create_menubar(self):
        menubar = QMenuBar(self)

        # --- Menu File ---
        file_menu = QMenu(self.translations.get("file", "File"), self)

        export_bin_action = QAction(self.translations.get("export_bin", "Open bin file in explorer"), self)
        export_bin_action.triggered.connect(self.export_bin)

        delete_file_action = QAction(self.translations.get("delete_stats_file", "Delete stats file"), self)
        delete_file_action.triggered.connect(self.delete_current_stats_file)


        exit_action = QAction(self.translations.get("exit", "Exit"), self)
        exit_action.triggered.connect(self._on_exit_action)

        file_menu.addAction(export_bin_action)
        file_menu.addAction(delete_file_action)
        file_menu.addSeparator() 
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)

    

        # --- Menu Edit ---
        edit_menu = QMenu(self.translations.get("edit", "Edit"), self)
        # Global search line
        if not hasattr(self, 'global_search_line'):
            self.global_search_line = QLineEdit()
            self.global_search_line.setPlaceholderText(self.translations.get("in_column_search_placeholder", ))
            self.global_search_line.setFixedWidth(200)
            self.global_search_line.textChanged.connect(self.global_search_in_table)
        search_widget = QWidget(self)
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(8, 2, 8, 2)
        search_layout.addWidget(QLabel(self.translations.get("in_column_search"), self))
        search_layout.addWidget(self.global_search_line)
        search_action = QWidgetAction(self)
        search_action.setDefaultWidget(search_widget)
        edit_menu.addSeparator()
        edit_menu.addAction(search_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.replace_in_column_action)
        edit_menu.addSeparator() 
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator() 
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.delete_action)
        edit_menu.addSeparator()
        # Columns submenu
        self.columns_menu = QMenu(self.translations.get("columns", "Columns"), self)
        self.column_actions = {}

        for i, header in enumerate(self.headers):
            checkbox = QCheckBox(header)
            checkbox.setChecked(True)
            if header in ["key", "ukrainian"]:
                checkbox.setEnabled(False)
            else:
                checkbox.toggled.connect(lambda state, h=header: self.set_column_visible(h, state))
                checkbox.toggled.connect(self.stretch_columns)
            action = QWidgetAction(self)
            action.setDefaultWidget(checkbox)
            self.columns_menu.addAction(action)
            self.column_actions[header] = checkbox
            

        edit_menu.addMenu(self.columns_menu)
        menubar.addMenu(edit_menu)

        # --- Menu Export/Import ---
        export_import_menu = QMenu(self.translations.get("export_import", "Export/Import"), self)
        export_all_action = QAction(self.translations.get("export_all", "Export to CSV (all languages)"), self)
        export_all_action.triggered.connect(self.export_csv_all)
        export_for_translate_action = QAction(self.translations.get("export_for_translate", "Export to CSV for translation"), self)
        export_for_translate_action.triggered.connect(self.export_csv_for_translate)
        import_action = QAction(self.translations.get(
            "import_csv", "Import from CSV"), self)
        import_action.triggered.connect(self.import_csv)
        export_import_menu.addAction(export_all_action)
        export_import_menu.addAction(export_for_translate_action)
        export_import_menu.addSeparator() 
        export_import_menu.addAction(import_action)
        menubar.addMenu(export_import_menu)



        # --- Menu Save ---
        save_menu = QMenu(self.translations.get("save", "Save"), self)
        save_known_action = QAction(self.translations.get(
            "save_bin_known", "Save bin file for yourself"), self)
        save_known_action.triggered.connect(self.save_bin_know)
        save_unknown_action = QAction(self.translations.get(
            "save_bin_unknown", "Save bin file to Steam folder"), self)
        save_unknown_action.triggered.connect(self.save_bin_unknow)
        save_menu.addAction(save_known_action)
        save_menu.addAction(save_unknown_action)
        menubar.addMenu(save_menu)

        # --- File stats list ---
        show_stats_action = QAction(self.translations.get("show_user_game_stats"), self)
        show_stats_action.triggered.connect(self.show_user_game_stats_list)
        menubar.addAction(show_stats_action)
 

        # --- Menu Language ---
        language_menu = QMenu(self.translations.get("language"), self)
        for lang in LANG_FILES.keys():
            action = QAction(lang, self)
            action.triggered.connect(lambda checked, l=lang: self.change_language(l))
            language_menu.addAction(action)
        menubar.addMenu(language_menu) 

        # --- About Button ---
        about_action = QAction(self.translations.get("about", "About"), self)
        about_action.triggered.connect(
            lambda: QMessageBox.information(
                self,
                self.translations.get("about_app", "About App"),
                self.translations.get("about_message", "About message text")
            )
        )
        menubar.addAction(about_action)

        # Adding menubar to the layout
        self.setMenuWidget(menubar)



    def change_language(self, lang):
        self.settings.setValue("language", lang)
        self.settings.sync()
        self.language = lang
        self.translations = self.load_language(lang)
        self.refresh_ui_texts()

    def refresh_ui_texts(self):
        self.setWindowTitle(f"{self.translations.get('app_title')}{APP_VERSION}")
        self.stats_bin_path_path.setPlaceholderText(self.translations.get("man_select_file_label"))
        self.stats_bin_path_btn.setText(self.translations.get("man_select_file"))
        self.select_stats_bin_path_btn.setText(self.translations.get("get_ach"))
        self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
        self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
        self.steam_folder_path.setPlaceholderText(self.translations.get("steam_folder_label"))
        self.select_steam_folder_btn.setText(self.translations.get("select_steam_folder"))
        self.game_id_edit.setPlaceholderText(self.translations.get("game_id_label"))
        self.load_game_btn.setText(self.translations.get("get_ach"))
        self.clear_game_id.setText(self.translations.get("clear_and_paste"))
        self.abo_label.setText(self.translations.get("OR"))
        self.steam_group.setTitle(self.translations.get("indirect_file_sel_label"))
        self.stats_group.setTitle(self.translations.get("man_file_sel_label"))
        self.copy_action.setText(self.translations.get("copy", "Copy"))
        self.paste_action.setText(self.translations.get("paste", "Paste"))
        self.cut_action.setText(self.translations.get("cut", "Cut"))
        self.delete_action.setText(self.translations.get("delete", "Delete"))
        self.redo_action.setText(self.translations.get("redo", "Redo"))
        self.undo_action.setText(self.translations.get("undo", "Undo"))
        self.replace_in_column_action.setText(self.translations.get("replace_in_column", "Replace"))
        if hasattr(self, 'global_search_line') and self.global_search_line is not None:
            self.global_search_line.setPlaceholderText(self.translations.get("in_column_search_placeholder"))
        self.create_menubar()
        for header, action in getattr(self, "column_actions", {}).items():
            col = self.headers.index(header)
            action.setChecked(not self.table.isColumnHidden(col))
        self.version()
        self.gamename()

    def load_language(self, language):
        path = resource_path(LANG_FILES[language])
        return load_json_with_fallback(path)

    def set_column_visible(self, header, visible):
        try:
            col = self.headers.index(header)
            self.table.setColumnHidden(col, not visible)        
        except ValueError:
            pass



    def stretch_columns(self, min_width: int = 120):
        # Stretch columns to fit the table width or set to min_width with scrollbar
        if self.table.columnCount() == 0:
            return

        available_width = self.table.viewport().width()
        total_min_width = self.table.columnCount() * min_width

        if total_min_width <= available_width:
            # If all columns fit — stretch them evenly
            for i in range(self.table.columnCount()):
                self.header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        else:
            # If not — set to min_width and enable horizontal scrollbar
            for i in range(self.table.columnCount()):
                self.header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.table.setColumnWidth(i, min_width)



    def on_steam_path_changed(self, text):
        # Update steam folder path when text changes
        self.steam_folder = text.strip()
        self.settings.setValue("UserSteamPath", self.steam_folder)
        self.settings.sync()

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
        
    def game_id(self):
        text = self.game_id_edit.text().strip()

        # Collect ID from URL if full link is provided
        match = re.search(r'/app/(\d+)', text)
        if match:
            return match.group(1)

        # If only digits are provided, return as is
        if text.isdigit():
            return text

        return None
                
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
        chunks = split_chunks(self.raw_data)
        self.chunks = chunks
        all_rows = []
        all_columns = set()
        for chunk in chunks:
            key = extract_key_and_data(chunk)
            if not key:
                continue
            words = extract_words(chunk)
            values = extract_values(chunk, words)
            word_counts = {}
            unique_row = {'key': key}
            description_row = {'key': f'{key}_opis'}
            for w, val in zip(words, values):
                count = word_counts.get(w, 0)
                if count == 0:
                    unique_row[w] = val
                else:
                    if w in description_row:
                        description_row[w] += '; ' + val
                    else:
                        description_row[w] = val
                word_counts[w] = count + 1
            all_rows.append(unique_row)
            if len(description_row) > 1:
                all_rows.append(description_row)
            for r in [unique_row, description_row]:
                for col in r.keys():
                    if col != 'key':
                        all_columns.add(col)
        # If 'ukrainian' column is missing, add it with empty values
        for row in all_rows:
            if 'ukrainian' not in row:
                row['ukrainian'] = ''

        # Fill 'english' column if missing
        for row in all_rows:
            if 'english' not in row:
                row['english'] = ''

        # Define headers: key, ukrainian, english, then others alphabetically
        all_columns = set()
        for row in all_rows:
            for col in row:
                if col != 'key':
                    all_columns.add(col)
        headers = ['key', 'ukrainian', 'english'] + sorted(all_columns - {'ukrainian', 'english'})

        self.headers = self.prioritize_headers(headers)

        self.data_rows = all_rows
        self.table.clear()
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(len(all_rows))
        for row_i, row in enumerate(all_rows):
            for col_i, col_name in enumerate(self.headers):
                value = row.get(col_name, '')
                self.table.setItem(row_i, col_i, QTableWidgetItem(value))
        if 'ukrainian' not in self.headers:
            self.headers.append('ukrainian')
            for row in self.data_rows:
                row['ukrainian'] = ''
        self.stretch_columns()
        self.update_row_heights()
        self.create_menubar()
        self.version()
        self.gamename()
        msg = self.translations.get("records_loaded").format(count=len(all_rows))
        QMessageBox.information(self, self.translations.get("success"), msg)
       


    def export_csv_all(self):
        fname, _ = QFileDialog.getSaveFileName(self, self.translations.get("export_csv_all_file_dialog"), '', 'CSV Files (*.csv)')
        if not fname:
            return
        try:
            with open(fname, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                writer.writeheader()
                for row in self.data_rows:
                    writer.writerow(row)
            QMessageBox.information(self, self.translations.get("success"), self.translations.get("csv_saved"))
        except Exception as e:
            QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_cannot_save')}{e}")


    def export_csv_for_translate(self):
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
            with open(fname, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['key', 'english', 'translation', context_col])
                for row in self.data_rows:
                    writer.writerow([
                        row.get('key', ''),
                        row.get('english', ''),
                        row.get('ukrainian', ''),  
                        row.get(context_col, ''),
                    ])
            QMessageBox.information(self, self.translations.get("success"), self.translations.get("csv_saved"))
        except Exception as e:
            QMessageBox.warning(self, self.translations.get("error"), str(e))

    def import_csv(self):
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
            with open(fname, 'r', encoding='utf-8') as csvfile:
                rows = list(csv.reader(csvfile))
                if not rows:
                    raise Exception(self.translations.get("error_empty"))
                header = rows[0]
                key_idx = header.index('key')
                translation_idx = header.index('translation')
                key_to_row = {row['key']: row for row in self.data_rows}
                for csv_row in rows[1:]:
                    if len(csv_row) <= max(key_idx, translation_idx):
                        continue
                    key = csv_row[key_idx]
                    val = csv_row[translation_idx].strip()
                    if key and key in key_to_row and val:
                        key_to_row[key][import_col] = val
            self.refresh_table()
            QMessageBox.information(self, self.translations.get("success"), self.translations.get("import_success"))
        except Exception as e:
            QMessageBox.warning(self, self.translations.get("error"), str(e))


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
       
            
            
    def replace_lang_in_bin(self):
        lang_columns = [col for col in self.data_rows[0].keys() if col != "key"]
        file_path = self.get_stats_bin_path()
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            return

        cleaned = bytearray(data)
        for selected_column in lang_columns:
            values = [row.get(selected_column, '') for row in self.data_rows]
            if selected_column == "english":
                english_marker = b'\x01english\x00'
                output = bytearray()
                i = 0
                v_idx = 0
                while i < len(cleaned):
                    idx = cleaned.find(english_marker, i)
                    if idx == -1:
                        output.extend(cleaned[i:])
                        break
                    output.extend(cleaned[i:idx + len(english_marker)])
                    i = idx + len(english_marker)
                    end = cleaned.find(b'\x00', i)
                    if end == -1:
                        break
                    if v_idx < len(values):
                        val = values[v_idx]
                        output.extend(val.encode("utf-8"))
                    output.extend(b'\x00')
                    i = end + 1
                    v_idx += 1
                cleaned = output
            else:
                # Delete old markers of this language
                marker = b'\x01' + selected_column.encode("utf-8") + b'\x00'
                new_cleaned = bytearray()
                i = 0
                while i < len(cleaned):
                    idx = cleaned.find(marker, i)
                    if idx == -1:
                        new_cleaned.extend(cleaned[i:])
                        break
                    new_cleaned.extend(cleaned[i:idx])
                    i = idx + len(marker)
                    end = cleaned.find(b'\x00', i)
                    if end == -1:
                        break
                    i = end + 1
                cleaned = new_cleaned

                # Insert new markers and values
                english_marker = b'\x01english\x00'
                output = bytearray()
                i = 0
                v_idx = 0
                while i < len(cleaned):
                    idx = cleaned.find(english_marker, i)
                    if idx == -1:
                        output.extend(cleaned[i:])
                        break
                    output.extend(cleaned[i:idx])
                    # Insert new marker if there is a value
                    if v_idx < len(values):
                        val = values[v_idx]
                        if val:
                            output.extend(b'\x01' + selected_column.encode("utf-8") + b'\x00' + val.encode("utf-8") + b'\x00')
                    output.extend(english_marker)
                    i = idx + len(english_marker)
                    end = cleaned.find(b'\x00', i)
                    if end == -1:
                        break
                    output.extend(cleaned[i:end+1])
                    i = end + 1
                    v_idx += 1
                cleaned = output
        return cleaned

        

    def export_bin(self):
        filepath = os.path.abspath(self.get_stats_bin_path())
        if not os.path.isfile(filepath):
            QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_no_file')}{filepath}")
            return
        folder = os.path.dirname(filepath)
        if sys.platform == "win32":
            subprocess.run(f'explorer /select,"{filepath}"')
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R", filepath])
        else:
            candidates = [
                ["nautilus", "--select", filepath],
                ["dolphin", "--select", filepath],
                ["thunar", "--select", filepath],
                ["nemo", "--browser", "--select", filepath]
            ]
            for cmd in candidates:
                if shutil.which(cmd[0]):
                    try:
                        subprocess.run(cmd, check=True)
                        return
                    except Exception:
                        continue
            try:
                subprocess.run(["xdg-open", folder])
            except Exception as e:
                QMessageBox.warning(self, self.translations.get("error"), f"{self.translations.get('error_cannot_open')}{e}")
        
        
  

    def save_bin_unknow(self):
        # Save to Steam folder
        self.sync_table_to_data_rows()
        datas = self.replace_lang_in_bin()
        if datas is None:
            QMessageBox.warning(self,
                                self.translations.get("error"),
                                self.translations.get("error_no_data_to_save"))
            return

        game_id = self.current_game_id()
        if not game_id:
            QMessageBox.warning(self,
                                self.translations.get("error"),
                                self.translations.get("error_no_id"))
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
            QMessageBox.information(
                self,
                self.translations.get("success"),
                self.translations.get("in_steam_folder_saved")
            )
            self.set_modified(False)
        except Exception as e:
            QMessageBox.critical(
                self,
                self.translations.get("error"),
                f"{self.translations.get('error_cannot_save')}{e}"
            )
            
  
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
            QMessageBox.warning(self, self.translations.get("error"), self.translations.get("error_no_data_to_save"))
            return

        try:
            with open(save_path, "wb") as f:
                f.write(datas)
            msg5 = self.translations.get("save_where_msg").format(save_path=save_path)
            QMessageBox.information(self, self.translations.get("success"), msg5)
        except Exception as e:
            QMessageBox.critical(self, self.translations.get("error"), f"{self.translations.get('error_cannot_save')}{e}")


        

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



    def detect_steam_path(self):
        home = os.path.expanduser("~")
        possible_paths = [
            # Стандартні Linux/Mac шляхи
            os.path.join(home, ".steam", "steam"),
            os.path.join(home, ".steam", "Steam"),
            os.path.join(home, ".local", "share", "Steam"),
            os.path.join(home, ".local", "share", "steam"),
            os.path.join(home, ".steam", "root"),
            os.path.join(home, ".steam", "Root"),
            # Snap версія Steam
            os.path.join(home, "snap", "steam", "common", ".local", "share", "Steam"),
            os.path.join(home, "snap", "steam", "common", ".steam", "steam"),
            os.path.join(home, "snap", "steam", "common", ".steam", "Steam"),
            os.path.join(home, "snap", "steam", "common", ".steam", "root"),
            os.path.join(home, "snap", "steam", "common", ".steam", "Root"),
        ]
        # Windows detection (як раніше)
        if sys.platform == "win32":
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam") as key:
                    steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                    steam_path = os.path.realpath(steam_path)
                    if os.path.exists(steam_path):
                        return steam_path
            except Exception:
                fallback = "C:\\Program Files (x86)\\Steam"
                if os.path.exists(fallback):
                    return fallback
                return ""
        else:
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return ""

    def prioritize_headers(self, headers):
        headers = [h for h in headers if h != 'key']
        prioritized = ['key']
        if 'ukrainian' in headers:
            prioritized.append('ukrainian')
            headers.remove('ukrainian')
        if 'english' in headers:
            prioritized.append('english')
            headers.remove('english')
        return prioritized + headers
         
    def version(self):
        path = self.get_stats_bin_path()

        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            if hasattr(self, "version_label"):
                self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
            return None

        marker = b"\x01version\x00"
        pos = data.find(marker)

        if pos == -1:
            if hasattr(self, "version_label"):
                self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
            return None

        start = pos + len(marker)
        end = data.find(b"\x00", start)
        if end == -1:
            if hasattr(self, "version_label"):
                self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")
            return None

        # Fetch version string
        ver_str = data[start:end].decode("utf-8", errors="ignore").strip()
        try:
            version_number = int(ver_str)
        except ValueError:
            version_number = None

        if hasattr(self, "version_label"):
            if version_number is not None:
                self.version_label.setText(f"{self.translations.get('file_version')}{version_number}")
            else:
                self.version_label.setText(f"{self.translations.get('file_version')}{self.translations.get('unknown')}")

        return version_number

        
        
        
    def gamename(self):
        path = self.get_stats_bin_path()

        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            if hasattr(self, "gamename_label"):
                self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
            return None

        marker = b"\x01gamename\x00"
        pos = data.find(marker)

        if pos == -1:
            if hasattr(self, "gamename_label"):
                self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
            return None

        # Fetch game name string
        start = pos + len(marker)
        end = data.find(b"\x00", start)
        if end == -1:
            if hasattr(self, "gamename_label"):
                self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
            return None

        name = data[start:end].decode("utf-8", errors="ignore").strip()

        if hasattr(self, "gamename_label"):
            if name:
                self.gamename_label.setText(f"{self.translations.get('gamename')}{name}")
            else:
                self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")


        return name



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


    def show_find_replace_dialog(self):   
        dlg = FindReplaceDialog(self, self.headers)
        dlg.exec()

    def show_user_game_stats_list(self):
        import re
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
                chunks = split_chunks(file_data)
                achievement_count = sum(1 for chunk in chunks if chunk.count(b'\x01english\x00') >= 2)
            except Exception:
                achievement_count = "?"
            # Temporarily set game ID and steam folder to load version and name
            self.game_id_edit.setText(game_id)
            self.steam_folder = self.steam_folder_path.text().strip()
            version = self.version()
            gamename = self.gamename()
            stats_list.append((
                fname,
                str(version) if version is not None else "?",
                gamename if gamename else "?",
                game_id,
                str(achievement_count)
            ))
        # Restore original values
        self.game_id_edit.setText(orig_game_id)
        self.steam_folder = orig_steam_folder
        # Show dialog
        dlg = UserGameStatsListDialog(self, stats_list)
        dlg.exec()


    def global_search_in_table(self, text):
        search_text = text.strip().lower()

        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                
                    

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

    def handle_game_id_action(self):
        game_id = self.game_id()
        if game_id:
            self.load_steam_game_stats()
        else:
            self.game_id_edit.clear()

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

            msg4 = self.translations.get("save_where_msg")
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

    def sync_table_to_data_rows(self):
        # Sync changes from table widget back to data_rows
        rows = min(self.table.rowCount(), len(self.data_rows))
        for row_i in range(rows):
            for col_i, header in enumerate(self.headers):
                item = self.table.item(row_i, col_i)
                self.data_rows[row_i][header] = item.text() if item else ''

    def current_game_id(self):
        # Return game ID based on current mode (manual or steam path)
        if self.force_manual_path:
            manual_path = self.stats_bin_path_path.text().strip()
            import re
            m = re.search(r'UserGameStatsSchema_(\d+)\.bin$', manual_path)
            if m:
                return m.group(1)
        return self.game_id()
    


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
        if confirm_box.clickedButton() is btn_CSV:
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


def main():
    global window
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    language = choose_language()

    # Load translations for warning (default to English if not set yet)
    settings = QSettings("Vena", "Steam Achievement Localizer")
    language = settings.value("language", "English")
    translations = load_json_with_fallback(resource_path(LANG_FILES.get(language, LANG_FILES["English"])))


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
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

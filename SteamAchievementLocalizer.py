import sys
import csv
import re
import os
import binascii
import subprocess
import winreg 
import json
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon, QColor, QBrush, QAction
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QHBoxLayout,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QFrame, QGroupBox, QHeaderView,
    QInputDialog, QMenu, QMenuBar, 
)


EXCLUDE_WORDS = {b'max', b'maxchange', b'min', b'token', b'name', b'icon', b'hidden', b'icon_gray', b'Hidden',b'', b'russian',b'Default',b'gamename',b'id',b'incrementonly',b'max_val',b'min_val',b'operand1',b'operation',b'type',b'version'}

LANG_FILES = {
    "English": "assets/lang_en.json",
    "Українська": "assets/lang_ua.json"
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
    return None
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
    
class BinParserGUI(QWidget):
    def __init__(self, language="English"):
        super().__init__()
                
        self.language = language
        self.translations = self.load_language(language)
        self.setWindowTitle(f"{self.translations.get('app_title')}{APP_VERSION}")
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        
        self.setMinimumSize(800, 800)
        self.set_window_size()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        

        self.settings = QSettings("Vena", "Steam Achievement Localizer")
        self.default_steam_path = self.detect_steam_path()
        
        
        
        self.force_manual_path = False  

        self.create_menubar()
        
        # --- File localization selection ---
        stats_bin_path_layout = QHBoxLayout()
        self.stats_bin_path_label = QLabel(self.translations.get("man_select_file_label"))
        self.stats_bin_path_path = QLineEdit()
        self.stats_bin_path_path.textChanged.connect(lambda text: self.settings.setValue("LastEnteredFilePath", text))
        self.stats_bin_path_btn = QPushButton(self.translations.get("man_select_file"))
        self.stats_bin_path_btn.clicked.connect(self.stats_bin_path_search)
        self.select_stats_bin_path_btn = QPushButton(self.translations.get("get_ach"))
        self.select_stats_bin_path_btn.clicked.connect(self.select_stats_bin_path)
        stats_bin_path_layout.addWidget(self.stats_bin_path_label)
        stats_bin_path_layout.addWidget(self.stats_bin_path_path)
        stats_bin_path_layout.addWidget(self.stats_bin_path_btn)
        stats_bin_path_layout.addWidget(self.select_stats_bin_path_btn)
        
        # --- Frame ---
        stats_group = QGroupBox(self.translations.get("man_file_sel_label"))
        stats_group.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        stats_group.setLayout(stats_bin_path_layout)
        self.layout.addWidget(stats_group)   
        
        
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
        self.steam_folder_label = QLabel(
            self.translations.get("steam_folder_label"))
        self.steam_folder_path = QLineEdit()
        self.steam_folder_path.textChanged.connect(self.on_steam_path_changed)
        self.select_steam_folder_btn = QPushButton(self.translations.get("select_steam_folder"))
        self.select_steam_folder_btn.clicked.connect(self.select_steam_folder)
        steam_folder_layout.addWidget(self.steam_folder_label)
        steam_folder_layout.addWidget(self.steam_folder_path)
        steam_folder_layout.addWidget(self.select_steam_folder_btn)

        
        self.set_steam_folder_path()
      
        # --- Game ID selection ---
        game_id_layout = QHBoxLayout()
        self.game_id_label = QLabel(self.translations.get("game_id_label"))
        self.game_id_edit = QLineEdit()
        self.game_id_edit.textChanged.connect(lambda text: self.settings.setValue("LastEnteredID", text))
        self.load_game_btn = QPushButton(self.translations.get("get_ach"))
        self.load_game_btn.clicked.connect(self.load_steam_game_stats)
        self.clear_game_id = QPushButton(self.translations.get("clear_and_paste"))
        self.clear_game_id.pressed.connect(lambda: ( 
            self.game_id_edit.clear(),
            self.game_id_edit.setText(QApplication.clipboard().text())
        ))
        game_id_layout.addWidget(self.game_id_label)
        game_id_layout.addWidget(self.game_id_edit)
        game_id_layout.addWidget(self.load_game_btn)
        game_id_layout.addWidget(self.clear_game_id)

        
        # --- Frame ---
        steam_group_layout = QVBoxLayout()
        steam_group_layout.addLayout(steam_folder_layout)
        steam_group_layout.addLayout(game_id_layout)
        steam_group = QGroupBox(self.translations.get("indirect_file_sel_label"))
        steam_group.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        steam_group.setLayout(steam_group_layout)
        self.layout.addWidget(steam_group)
        

       
        
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

        # Vertical separator
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.VLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        lang_layout.addWidget(line3)

        # 4. Language selection
        lang_select_layout = QHBoxLayout()
        lang_select_layout.addWidget(QLabel(self.translations.get("lang_sel")))
        self.context_lang_combo = QComboBox()
        self.context_lang_combo.setFixedSize(150, 25)
        self.context_lang_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")
        lang_select_layout.addWidget(self.context_lang_combo)
        lang_layout.addLayout(lang_select_layout)



        # --- Frame ---
        box = QGroupBox("")  # без заголовку
        box.setFlat(False)
        box.setLayout(lang_layout)
        self.layout.addWidget(box)


        # --- Search ---
        self.headers = []
        search_layout = QHBoxLayout()
        self.search_column_combo = QComboBox()
        self.search_column_combo.setFixedSize(150, 25)
        self.search_column_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.search_column_combo.addItems([h for h in self.headers if h != 'key']) 
        search_layout.addWidget(QLabel("Пошук у стовпці:"))
        search_layout.addWidget(self.search_column_combo)
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Пошук слова в стовпці")
        self.search_line.textChanged.connect(self.search_in_table)
        search_layout.addWidget(self.search_line)
        self.layout.addLayout(search_layout)
        
        # --- Save buttons ---
        btn_layout_2 = QHBoxLayout()
        self.save_bin_unknow_btn = QPushButton("Зберегти бінарник у теці Стіму") 
        self.save_bin_unknow_btn.clicked.connect(self.save_bin_unknow) 
        self.save_bin_know_btn = QPushButton("Зберегти бінарник для себе") 
        self.save_bin_know_btn.clicked.connect(self.save_bin_know)
        btn_layout_2.addWidget(self.save_bin_know_btn)
        btn_layout_2.addWidget(self.save_bin_unknow_btn)
        self.layout.addLayout(btn_layout_2)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.itemChanged.connect(self.on_table_item_changed)
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
    
                
    def create_menubar(self):
        menubar = QMenuBar(self)

        # --- Menu File ---
        file_menu = QMenu(self.translations.get("file", "File"), self)
        exit_action = QAction(self.translations.get("exit", "Exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)

        # --- Menu Language ---
        language_menu = QMenu(self.translations.get("language"), self)
        for lang in LANG_FILES.keys():
            action = QAction(lang, self)
            action.triggered.connect(lambda checked, l=lang: self.change_language(l))
            language_menu.addAction(action)
        menubar.addMenu(language_menu)


        # --- Menu Export ---
        export_menu = QMenu(self.translations.get("export", "Export"), self)
        export_bin_action = QAction(self.translations.get("export_bin", "Open bin file in explorer"), self)
        export_bin_action.triggered.connect(self.export_bin)
        export_all_action = QAction(self.translations.get("export_all", "Export to CSV (all languages)"), self)
        export_all_action.triggered.connect(self.export_csv_all)
        export_for_translate_action = QAction(self.translations.get("export_for_translate", "Export to CSV for translation"), self)
        export_for_translate_action.triggered.connect(self.export_csv_for_translate)
        export_menu.addAction(export_bin_action)
        export_menu.addAction(export_all_action)
        export_menu.addAction(export_for_translate_action)
        menubar.addMenu(export_menu)

        # --- Menu Import ---
        import_menu = QMenu(self.translations.get("import", "Import"), self)
        import_action = QAction(self.translations.get(
            "import_csv", "Import from CSV"), self)
        import_action.triggered.connect(self.import_csv)
        import_menu.addAction(import_action)
        menubar.addMenu(import_menu)


        # --- Menu About ---
        about_menu = QMenu(self.translations.get("about", "About"), self)  
        about_action = QAction(self.translations.get("about_app", "About App"), self)
        about_action.triggered.connect(
            lambda: QMessageBox.information(
                self,
                self.translations.get("about_app", "About App"),
                self.translations.get("about_message", "")
            )
        )
        about_menu.addAction(about_action)
        menubar.addMenu(about_menu)

        # Adding menubar to the layout
        self.layout.setMenuBar(menubar)


    def change_language(self, lang):
        # Зберігаємо вибір мови
        self.settings.setValue("language", lang)
        self.settings.sync()

        # Показуємо повідомлення про перезапуск
        QMessageBox.information(
            self, "Info", "Language changed. The application will restart to apply the new language.")
        # Перезапускаємо програму з новою мовою
        python = sys.executable
        subprocess.Popen([python] + sys.argv)
        self.close() 

    def load_language(self, language):
        path = resource_path(LANG_FILES[language])
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except UnicodeDecodeError:
            # fallback для Windows-кодування
            with open(path, "r", encoding="cp1251") as f:
                return json.load(f)



    def stretch_columns(self, min_width: int = 120):
        """Розтягує колонки з мінімальною шириною"""
        if self.table.columnCount() == 0:
            return

        available_width = self.table.viewport().width()
        total_min_width = self.table.columnCount() * min_width

        if total_min_width <= available_width:
            # 🔄 якщо колонок мало — розтягуємо рівномірно на всю ширину
            for i in range(self.table.columnCount()):
                self.header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        else:
            # 📏 якщо колонок багато — мінімальна ширина + скрол
            for i in range(self.table.columnCount()):
                self.header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.table.setColumnWidth(i, min_width)



    def on_steam_path_changed(self, text):
        """Оновлення шляху Steam при зміні тексту"""
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

        # Витягує ID гри з будь-якого посилання, де є /app/123456
        match = re.search(r'/app/(\d+)', text)
        if match:
            return match.group(1)

        # Якщо просто число
        if text.isdigit():
            return text

        return None
                
    def select_steam_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Обрати теку Стіму", self.steam_folder
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
            QMessageBox.warning(self, "Помилка", "Введіть ID гри чи посилання на неї,\n яке ви знаєте зверху на сторінці крамниці Стім")
            return
        if not self.steam_folder:
            QMessageBox.warning(self, "Помилка", "Спочатку оберіть теку Стім")
            return
        path = self.get_stats_bin_path()
        try:
            with open(path, "rb") as f:
                self.raw_data = f.read()
        except FileNotFoundError:
            QMessageBox.warning(self, "Помилка", f"Файл не знайдено:\n{path}")
            return
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося відкрити файл:\n{e}")
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
        # Якщо 'ukrainian' не присутній у жодному рядку — додаємо
        for row in all_rows:
            if 'ukrainian' not in row:
                row['ukrainian'] = ''

        # Аналогічно для english (якщо хочеш)
        for row in all_rows:
            if 'english' not in row:
                row['english'] = ''

        # Після цього знову зібрати headers
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
        self.fill_context_lang_combo()
        self.update_search_column_combo()
        self.stretch_columns()
        self.version()
        self.gamename()
        QMessageBox.information(self, "Успіх", f"Завантажено {len(all_rows)} записів")
        


    def fill_context_lang_combo(self):
        if not self.headers:
            return
        self.context_lang_combo.clear()
        langs = [h for h in self.headers if h != 'key']
        if 'english' in langs:
            langs.remove('english')
            langs = ['english'] + langs
        self.context_lang_combo.clear()
        self.context_lang_combo.addItems([h for h in self.headers if h not in ['key']])

        if 'english' in langs:
            self.context_lang_combo.setCurrentIndex(0)
        elif langs:
            self.context_lang_combo.setCurrentIndex(0)
    def export_csv_all(self):
        fname, _ = QFileDialog.getSaveFileName(self, 'Зберегти CSV', '', 'CSV Files (*.csv)')
        if not fname:
            return
        try:
            with open(fname, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                writer.writeheader()
                for row in self.data_rows:
                    writer.writerow(row)
            QMessageBox.information(self, "Успіх", "CSV файл збережено")
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося зберегти файл: {e}")


    def export_csv_for_translate(self):
        QMessageBox.information(self, "Інформація", "Експорт у CSV для перекладу включає колонки: key, english, ukrainian та <b>вибрану мову контексту</b>.<br>Обрати мову контексту можна у полі <b>\"Вибір мови\"</b><br>Після перекладу заповніть колонку 'ukrainian' і імпортуйте файл назад у програму.")
        if 'english' not in self.headers:
            QMessageBox.warning(self, "Помилка", "Відсутня колонка 'english'")
            return
        key_col = 'key'
        translate_col = 'english'
        translated_col = 'ukrainian'
        context_col = self.context_lang_combo.currentText()
        if not context_col:
            QMessageBox.warning(self, "Помилка", "Оберіть мову контексту")
            return
        fname, _ = QFileDialog.getSaveFileName(self, "Зберегти CSV (для перекладу)", "", "CSV Files (*.csv)")
        if not fname:
            return
        try:
            with open(fname, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([key_col, translate_col, translated_col, context_col])
                for row in self.data_rows:
                    writer.writerow([
                        row.get(key_col, ''),
                        row.get(translate_col, ''),
                        row.get(translated_col, ''),
                        row.get(context_col, ''),
                    ])
            QMessageBox.information(self, "Успіх", "CSV для перекладу збережено")
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося зберегти файл: {e}")

    def import_csv(self):
        QMessageBox.information(self, "Інформація", "Імпорт CSV замінить вибрану мову на значення з колонки 'ukrainian', якщо вона заповнена.<br>Переконайтеся, що у файлі є колонки: 'key', 'ukrainian' і <b>вибрана мова контексту</b>.<br>Оберіть мову контексту у полі <b>\"Вибір мови\"</b> перед імпортом.")
        fname, _ = QFileDialog.getOpenFileName(self, "Відкрити CSV для імпорту", "", "CSV Files (*.csv)")
        if not fname:
            return

        context_lang = self.context_lang_combo.currentText()
        if not context_lang:
            QMessageBox.warning(self, "Помилка", "Оберіть мову для імпорту")
            return

        try:
            with open(fname, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
            # Перевірка, що потрібні колонки є у файлі
                if 'key' not in reader.fieldnames or 'ukrainian' not in reader.fieldnames or context_lang not in reader.fieldnames:
                    QMessageBox.warning(self, "Помилка", f"CSV має містити колонки: 'key', 'ukrainian', '{context_lang}'")
                    return

                key_to_row = {row['key']: row for row in self.data_rows}

            # Проходимо по CSV і оновлюємо дані у self.data_rows
                for csv_row in reader:
                    key = csv_row.get('key', '')
                    ukrainian_val = csv_row.get('ukrainian', '').strip()
                    if not key or key not in key_to_row:
                        continue

                # Якщо в колонці ukrainian є текст, замінюємо вибрану мову (context_lang) на нього
                    if ukrainian_val:
                        key_to_row[key][context_lang] = ukrainian_val

        # Оновлюємо таблицю з новими даними
            self.refresh_table()
            QMessageBox.information(self, "Успіх", "CSV імпортовано і дані оновлено")
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося імпортувати CSV:\n{e}")


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


    def print_selected_column(self):
        selected_column = self.context_lang_combo.currentText()
        if not selected_column:
            print("Колонку не вибрано.")
            return

        try:
            col_index = self.headers.index(selected_column)
        except ValueError:
            print(f"Колонка '{selected_column}' не знайдена у заголовках.")
            return

        print(f"--- Вміст колонки '{selected_column}' ---")
        for row_i in range(self.table.rowCount()):
            item = self.table.item(row_i, col_index)
            value = item.text() if item else ''
            print(value)
            

    def on_table_item_changed(self, item):
        row = item.row()
        col = item.column()
        header = self.headers[col]
        new_value = item.text()
        if 0 <= row < len(self.data_rows):
            self.data_rows[row][header] = new_value
            
            

    def replace_lang_in_bin(self):

        selected_column = self.context_lang_combo.currentText()
        if not selected_column:
            QMessageBox.warning(self, "Помилка", f"Колонку не вибрано")
            return

        try:
            col_index = self.headers.index(selected_column)
        except ValueError:
            print(f"Колонка '{selected_column}' не знайдена у заголовках.")
            return

        # Значення для вставки
        values = []
        for row_i in range(self.table.rowCount()):
            item = self.table.item(row_i, col_index)
            value = item.text() if item else ''
            values.append(value)

        file_path = self.get_stats_bin_path()

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            print("Файл не знайдено:", file_path)
            return

        output = bytearray()
        i = 0
        v_idx = 0

        marker = b'\x01' + selected_column.encode("utf-8") + b'\x00'

        if marker in data:
            # 🔄 Мова вже існує — редагуємо значення
            while i < len(data):
                idx = data.find(marker, i)
                if idx == -1:
                    output.extend(data[i:])
                    break

                # Копіюємо до і включно з маркером
                output.extend(data[i:idx + len(marker)])
                i = idx + len(marker)

                end = data.find(b'\x00', i)
                if end == -1:
                    print("Не вдалося знайти кінець рядка.")
                    return

                # Заміна значення
                if v_idx < len(values):
                    new_text = values[v_idx].encode("utf-8")
                else:
                    new_text = b''

                output.extend(new_text + b'\x00')
                i = end + 1
                v_idx += 1

        else:
            # ➕ Мови ще нема — вставляємо перед english
            english_marker = b'\x01english\x00'
            while i < len(data):
                idx = data.find(english_marker, i)
                if idx == -1:
                    output.extend(data[i:])
                    break

                output.extend(data[i:idx])

                # Вставляємо український переклад
                if v_idx < len(values):
                    ukr_text = values[v_idx].encode("utf-8")
                else:
                    ukr_text = b''

                output.extend(b'\x01ukrainian\x00' + ukr_text + b'\x00')
                output.extend(english_marker)

                i = idx + len(english_marker)
                end = data.find(b'\x00', i)
                if end == -1:
                    print("Не вдалося знайти кінець рядка після english.")
                    return
                output.extend(data[i:end+1])
                i = end + 1
                v_idx += 1

        return output


        

    def export_bin(self):
        filepath = os.path.abspath(self.get_stats_bin_path())
        subprocess.run(f'explorer /select,"{filepath}"')
        
        
  

    def save_bin_unknow(self):
        datas = self.replace_lang_in_bin()
        if self.force_manual_path is True:
            QMessageBox.warning(self, "Помилка", "Ти завантажив файл з якоїсь іншої теки, шуруй зберігай де-інде")
            return
        if datas is None:
            QMessageBox.warning(self, "Помилка", "Спершу завантажте файл досягнень")
            return

        save_path = os.path.join(
            self.steam_folder, "appcache", "stats",
            f"UserGameStatsSchema_{self.game_id()}.bin"
        )
        try:
            with open(save_path, "wb") as f:
                f.write(datas)
            QMessageBox.information(self, "Готово", f"Файл збережено у теці Стіму")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти файл:\n{e}")
            
  
    def save_bin_know(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти змінений файл",
            self.get_stats_bin_path(),
            "Binary files (*.bin);;All files (*)"
        )

        if not save_path:
            return

        datas = self.replace_lang_in_bin()
        if datas is None:
            QMessageBox.warning(self, "Помилка", "Спершу завантажте файл досягнень")
            return

        try:
            with open(save_path, "wb") as f:
                f.write(datas)
            QMessageBox.information(self, "Готово", f"Файл збережено:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти файл:\n{e}")

    def search_in_table(self, text):
        col_name = self.search_column_combo.currentText()
        try:
            col_index = self.headers.index(col_name)
        except ValueError:
            return

        search_text = text.strip().lower()

        # Скидаємо фон і показуємо всі рядки спочатку (лише у вибраному стовпці!)
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QBrush())
            self.table.setRowHidden(row, False)

        # Пошук і підсвічування
        if not search_text:
            return  # Якщо поле пошуку порожнє, нічого не виділяємо

        for row in range(self.table.rowCount()):
            item = self.table.item(row, col_index)
            if item and item.text().strip():
                if search_text in item.text().lower():
                    item.setBackground(QBrush(QColor("gray")))  # або інший пастельний колір
                    self.table.setRowHidden(row, False)
                else:
                    self.table.setRowHidden(row, True)
            else:
                self.table.setRowHidden(row, True)
                
    def update_search_column_combo(self):
        self.search_column_combo.clear()
        self.search_column_combo.addItems(self.headers)
        

    def set_steam_folder_path(self, force=False):
        path = self.settings.value("UserSteamPath", "") or ""
        if force or not path.strip():
            detected = self.detect_steam_path()
            if detected:
                path = detected
            else:
                fallback = "C:\\Program Files (x86)\\Steam"
                if os.path.exists(fallback):
                    path = fallback
                else:
                    QMessageBox.warning(self, "Увага", "Не вдалося знайти теку Steam автоматично")
                    path = ""

            self.settings.setValue("UserSteamPath", path)
            self.settings.sync()

        self.steam_folder_path.setText(path)


    def detect_steam_path(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam") as key:
                steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                steam_path = os.path.realpath(steam_path)
                if os.path.exists(steam_path):
                    return steam_path
        except Exception:
            return None
        return None

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

        # Витягаємо рядок і пробуємо перетворити на число
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

        # Після маркера йде текст назви
        start = pos + len(marker)
        end = data.find(b"\x00", start)
        if end == -1:
            if hasattr(self, "gamename_label"):
                self.gamename_label.setText(f"{self.translations.get('gamename')}{self.translations.get('unknown')}")
            return None

        name = data[start:end].decode("utf-8", errors="ignore").strip()

        if hasattr(self, "gamename_label"):
            self.gamename_label.setText(f"{self.translations.get('gamename')}{name if name else {self.translations.get('unknown')}}")


        return name



    def get_stats_bin_path(self):
        """Обирає шлях у залежності від кнопки"""
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
            "Обрати файл UserGameStatsSchema",
            "",
            "Binary files (*.bin);;All files (*)"
        )
        if file:  # тільки якщо щось вибрано
            self.stats_bin_path_path.setText(file)
        self.select_stats_bin_path()


    def select_stats_bin_path(self):
        path = self.stats_bin_path_path.text().strip()
        if not path:
            QMessageBox.warning(self, "Помилка", "Спочатку оберіть файл UserGameStatsSchema")
            return
        try:
            with open(path, "rb") as f:
                self.raw_data = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося відкрити файл:\n{e}")
            return
            
        self.force_manual_path = True
        self.parse_and_fill_table()
        self.version()
        self.gamename()


    def use_manual_path(self):
        self.force_manual_path = True

    def use_steam_path(self):
        self.force_manual_path = False
        self.set_steam_folder_path(force=True)


    

APP_VERSION = "7.5.0"  

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    language = choose_language()

    # Load translations for warning (default to English if not set yet)
    settings = QSettings("Vena", "Steam Achievement Localizer")
    language = settings.value("language", "English")
    try:
        with open(resource_path(LANG_FILES.get(language, LANG_FILES["English"])), "r", encoding="utf-8") as f:
            translations = json.load(f)
    except UnicodeDecodeError:
        with open(resource_path(LANG_FILES.get(language, LANG_FILES["English"])), "r", encoding="cp1251") as f:
            translations = json.load(f)
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

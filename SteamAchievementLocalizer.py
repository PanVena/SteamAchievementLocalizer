import sys
import csv
import re
import os
import binascii
import subprocess
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon, QColor, QBrush
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QHBoxLayout,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QComboBox
)


app = QApplication(sys.argv)
app.setStyle("Fusion")

EXCLUDE_WORDS = {b'token', b'name', b'icon', b'hidden', b'icon_gray', b'Hidden',b'', b'russian',b'Default',b'gamename',b'id',b'incrementonly',b'max_val',b'min_val',b'operand1',b'operation',b'type',b'version'}
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
    if key_match:
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
    
def resource_path(relative_path):
    """Дозволяє знайти шлях до ресурсів як у .py, так і у .exe"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class BinParserGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Локалізатор досягнень Стіму від Вени ver 0.000.00000.00000.000000003')
        self.resize(1000, 1000)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
        
        self.default_steam_path = r"C:\Program Files (x86)\Steam"
        self.steam_folder = self.default_steam_path
        
        # --- Вибір теки Steam ---
        steam_folder_layout = QHBoxLayout()
        self.steam_folder_label = QLabel("Тека Стіму(якщо маєте її де-інде оберіть її):")
        self.steam_folder_path = QLineEdit()
        self.steam_folder_path.textChanged.connect(lambda text: (setattr(self, 'steam_folder', text.strip()), self.settings.setValue("UserSteamPath", self.steam_folder)))
        self.auto_select_steam_path = QPushButton("Обрати кореневу теку Стіму автоматично")
        self.auto_select_steam_path.clicked.connect(self.detect_steam_path)
        self.select_steam_folder_btn = QPushButton("Обрати кореневу теку Стіму вручну")
        self.select_steam_folder_btn.clicked.connect(self.select_steam_folder)
        steam_folder_layout.addWidget(self.steam_folder_label)
        steam_folder_layout.addWidget(self.steam_folder_path)
        steam_folder_layout.addWidget(self.auto_select_steam_path)
        steam_folder_layout.addWidget(self.select_steam_folder_btn)
        self.layout.addLayout(steam_folder_layout)
        
        self.settings = QSettings("Steam Achievement Localizer", "Steam Achievement Localizer")
        if self.settings.value("UserSteamPath"):
            self.steam_folder_path.setText(self.settings.value("UserSteamPath"))
        else:
            self.steam_folder_path.setText(self.default_steam_path)
            self.settings.setValue("UserSteamPath", self.steam_folder)
        
        # --- Введення ID гри ---
        game_id_layout = QHBoxLayout()
        self.game_id_label = QLabel("ID гри, або посиланння з крамниці Стім:")
        self.game_id_edit = QLineEdit()
        self.load_game_btn = QPushButton("Шукай ачівки(чи ачивки)!")
        self.load_game_btn.clicked.connect(self.load_steam_game_stats)
        game_id_layout.addWidget(self.game_id_label)
        game_id_layout.addWidget(self.game_id_edit)
        game_id_layout.addWidget(self.load_game_btn)
        self.layout.addLayout(game_id_layout)
        # Кнопки експорту/імпорту CSV
        btn_layout = QHBoxLayout()
        self.export_bin_btn = QPushButton('Бінарник у натуральному середовищі')
        self.export_bin_btn.clicked.connect(self.export_bin)
        self.export_all_btn = QPushButton('Експорт CSV (усе шо є)')
        self.export_all_btn.clicked.connect(self.export_csv_all)
        self.export_for_translate_btn = QPushButton('Експорт CSV (англійська і вибрана мова контексту)')
        self.export_for_translate_btn.clicked.connect(self.export_csv_for_translate)
        self.import_btn = QPushButton('Імпорт CSV з вашим перекладом')
        self.import_btn.clicked.connect(self.import_csv)
        btn_layout.addWidget(self.export_bin_btn)
        btn_layout.addWidget(self.export_all_btn)
        btn_layout.addWidget(self.export_for_translate_btn)
        btn_layout.addWidget(self.import_btn)
        self.layout.addLayout(btn_layout)
        
        # Вибір мови контексту
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("В разі питань, тґ:\n@Pan_Vena\nУ разі вдячності:\n4441 1111 2623 3299"))
        lang_layout.addWidget(QLabel("Вибір мови:"))
        self.context_lang_combo = QComboBox()
        lang_layout.addWidget(self.context_lang_combo)
        lang_layout.addWidget(QLabel(
            "*Для експорту у CSV виберіть собі окрему мову для контексту при перекладі<br>"
            "*Для імпорту оберіть english (воно впливає)<br>"
            "<b>*При збереженні бінарника впевніться, що вибрано english,<br>якщо звісно ви не хочете іншої мови замість української</b>"
        ))
        self.layout.addLayout(lang_layout)
        
        #Пошук
        self.headers = []  
        search_layout = QHBoxLayout()
        self.search_column_combo = QComboBox()
        self.search_column_combo.addItems([h for h in self.headers if h != 'key'])  # після ініціалізації headers
        search_layout.addWidget(QLabel("Пошук у стовпці:"))
        search_layout.addWidget(self.search_column_combo)
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Пошук слова в стовпці")
        self.search_line.textChanged.connect(self.search_in_table)
        search_layout.addWidget(self.search_line)
        self.layout.addLayout(search_layout)
        
        #Збереження
        btn_layout_2 = QHBoxLayout()
        self.save_bin_unknow_btn = QPushButton("Зберегти бінарник у теці Стіму") 
        self.save_bin_unknow_btn.clicked.connect(self.save_bin_unknow) 
        self.save_bin_know_btn = QPushButton("Зберегти бінарник для себе") 
        self.save_bin_know_btn.clicked.connect(self.save_bin_know)
        btn_layout_2.addWidget(self.save_bin_know_btn)
        btn_layout_2.addWidget(self.save_bin_unknow_btn)
        self.layout.addLayout(btn_layout_2)
                
        
        # Таблиця з даними
        self.table = QTableWidget()
        self.table.itemChanged.connect(self.on_table_item_changed)
        self.layout.addWidget(self.table)
        self.data_rows = []
        self.headers = []
        self.raw_data = b""
        self.chunks = []
        
        
    def game_id(self):
        text = self.game_id_edit.text().strip()

        # Регулярка, що витягує ID з будь-якого Steam-посилання
        match = re.search(r'store\.steampowered\.com/app/(\d+)', text)
        if match:
            return match.group(1)

        # Якщо просто число
        if text.isdigit():
            return text

        return None
                
    def select_steam_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Обрати теку Стіму", self.default_steam_path
        )
        if folder:
            self.steam_folder_path.setText(os.path.realpath(folder))

    def load_steam_game_stats(self):
        game_id = self.game_id()
        if not game_id:
            QMessageBox.warning(self, "Помилка", "Введіть ID гри чи посилання на неї,\n яке ви знаєте зверху на сторінці крамниці Стім")
            return
        if not self.steam_folder:
            QMessageBox.warning(self, "Помилка", "Спочатку оберіть теку Стім")
            return
        path = f"{self.steam_folder}/appcache/stats/UserGameStatsSchema_{game_id}.bin"
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
        all_columns = list(all_columns)
        if 'english' in all_columns:
            all_columns.remove('english')
            all_columns = ['english'] + sorted(all_columns)
        else:
            all_columns = sorted(all_columns)
        headers = ['key'] + all_columns
        self.headers = headers
        self.data_rows = all_rows
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(all_rows))
        for row_i, row in enumerate(all_rows):
            self.table.setItem(row_i, 0, QTableWidgetItem(row.get('key', '')))
            for col_i, col_name in enumerate(all_columns, start=1):
                self.table.setItem(row_i, col_i, QTableWidgetItem(row.get(col_name, '')))
        self.fill_context_lang_combo()
        self.update_search_column_combo()
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
        self.context_lang_combo.addItems(langs)
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
        for row_i, row in enumerate(self.data_rows):
            self.table.setItem(row_i, 0, QTableWidgetItem(row.get('key', '')))
            for col_i, col_name in enumerate(self.headers[1:], start=1):
                self.table.setItem(row_i, col_i, QTableWidgetItem(row.get(col_name, '')))

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
            
            
    def replace_english_in_bin(self):
        # Отримуємо назву колонки
        selected_column = self.context_lang_combo.currentText()
        if not selected_column:
            QMessageBox.warning(self, "Помилка", f"Колонку не вибрано")
          
            return

        try:
            col_index = self.headers.index(selected_column)
        except ValueError:
            print(f"Колонка '{selected_column}' не знайдена у заголовках.")
            return

        # Читаємо всі значення з колонки
        values = []
        for row_i in range(self.table.rowCount()):
            item = self.table.item(row_i, col_index)
            value = item.text() if item else ''
            values.append(value)

        # Шлях до вхідного бінарного файлу
        file_path = f"{self.steam_folder}/appcache/stats/UserGameStatsSchema_{self.game_id()}.bin"

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            print("Файл не знайдено:", file_path)
            return


  # Заміна значень
        marker = b'\x01english\x00'
        output = bytearray()
        i = 0
        v_idx = 0  # індекс значення з таблиці

        while i < len(data):
            idx = data.find(marker, i)
            if idx == -1:
                output.extend(data[i:])
                break

            output.extend(data[i:idx + len(marker)])
            i = idx + len(marker)

            end = data.find(b'\x00', i)
            if end == -1:
                print("Не вдалося знайти кінець рядка після мітки.")
                return

            i = end + 1  # пропускаємо старий рядок

            # Отримуємо нове значення
            new_val = values[v_idx] if v_idx < len(values) else ''
            output.extend(new_val.encode("utf-8") + b'\x00')
            v_idx += 1


        
        return output
        
        

    def export_bin(self):
        filepath = os.path.abspath(f"{self.steam_folder}/appcache/stats/UserGameStatsSchema_{self.game_id()}.bin")
        subprocess.run(f'explorer /select,"{filepath}"')
        
        
  
    def save_bin_unknow(self):
        datas = self.replace_english_in_bin()
        with open(f"{self.steam_folder}/appcache/stats/UserGameStatsSchema_{self.game_id()}.bin", "wb") as f: 
            f.write(datas)
        QMessageBox.information(self, "Готово", f"Файл збережено у теці Стіму")    
        
            
  
    def save_bin_know(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти змінений файл",
            f"{self.steam_folder}/appcache/stats/UserGameStatsSchema_{self.game_id()}.bin",
            "Binary files (*.bin);;All files (*)"
        )

        if save_path:
            try:
                datas = self.replace_english_in_bin()
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
        self.search_column_combo.addItems([h for h in self.headers if h != 'key'])
        
    def detect_steam_path(self):
        try:
            import winreg
            steam_app_path = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam")
            if steam_app_path:
                steam_folder_path = os.path.realpath(winreg.QueryValueEx(steam_app_path, "SteamPath")[0])
                if steam_folder_path != self.steam_folder_path.text():
                    self.steam_folder_path.setText(steam_folder_path)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося обрати теку Стіму автоматично:\n{e}")
        
        
def main():
    app = QApplication(sys.argv)
    window = BinParserGUI()
    window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()

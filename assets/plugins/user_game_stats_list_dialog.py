from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QLineEdit, QSizePolicy, QSpacerItem
from PyQt6.QtCore import Qt
import os
import re
from assets.plugins.highlight_delegate import HighlightDelegate

class UserGameStatsListDialog(QDialog):
    def __init__(self, parent, stats_list):
        super().__init__(parent)
        translations = getattr(self.parent(), "translations", {})
        self.setWindowTitle(parent.translations.get("user_game_stats_list"))
        self.setMinimumSize(720, 600)
        layout = QVBoxLayout()

        # --- In-column search ---
        search_layout = QHBoxLayout()
        search_label = QLabel(translations.get("in_column_search"), self)
        self.search_line = QLineEdit(self)
        self.search_line.setPlaceholderText(translations.get("in_column_search_placeholder"))
        self.search_line.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_line)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            translations.get("file_name"),
            translations.get("version"),
            translations.get("gamename_list"),
            translations.get("game_id"),
            translations.get("achievements_count")
        ])
        self.stats_list = stats_list
        self.fill_table(stats_list)
        self.table.resizeColumnsToContents()
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        layout.addWidget(self.table)

        self.highlight_delegate = HighlightDelegate(self.table)
        self.table.setItemDelegate(self.highlight_delegate)

        # --- Buttons and selected game display ---
        btn_box = QHBoxLayout()
        self.select_btn = QPushButton(translations.get("get_ach"))
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.select_game)
        btn_box.addWidget(self.select_btn)

        self.selected_gamename_label = QLabel("")
        self.selected_gamename_label.setWordWrap(True)
        self.selected_gamename_label.setMinimumWidth(350)  
        btn_box.addWidget(self.selected_gamename_label)
        btn_box.addStretch(1)

        close_btn = QPushButton(translations.get("close"))
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)

        layout.addLayout(btn_box)

        self.setLayout(layout)
        self.stretch_columns() 


        self.selected_row = None

    def fill_table(self, stats_list):
        self.table.setRowCount(len(stats_list))
        for row, (fname, version, gamename, game_id, achievement_count) in enumerate(stats_list):
            self.table.setItem(row, 0, QTableWidgetItem(str(fname)))

            item_version = QTableWidgetItem(str(version))
            item_version.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_version)

            self.table.setItem(row, 2, QTableWidgetItem(str(gamename)))

            item_id = QTableWidgetItem(str(game_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, item_id)

            item_ach = QTableWidgetItem(str(achievement_count))
            item_ach.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, item_ach)
        self.stretch_columns()

    def filter_table(self, text):
        text = text.strip().lower()
        filtered = []
        for row_data in self.stats_list:
            if not text or any(text in str(cell).lower() for cell in row_data):
                filtered.append(row_data)
        self.fill_table(filtered)
        self.selected_row = None
        self.select_btn.setEnabled(False)
        self.selected_gamename_label.setText("")

        # Update highlighting
        self.highlight_delegate.set_highlight(text)
        self.highlight_delegate.highlight_column = -1  
        self.table.viewport().update()

    def stretch_columns(self):
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            if i in (1,3, 4):
                header.setSectionResizeMode(i, self.table.horizontalHeader().ResizeMode.Interactive)
                self.table.setColumnWidth(i, 80)
            else:
                header.setSectionResizeMode(i, self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.viewport().update()
     
    def on_table_cell_clicked(self, row, col):
        self.table.selectRow(row)
        gamename = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        self.selected_gamename_label.setText(gamename)
        self.selected_row = row
        self.select_btn.setEnabled(True)

    def select_game(self):
        if self.selected_row is None:
            return
        item_id = self.table.item(self.selected_row, 3)
        if not item_id:
            return
        game_id = item_id.text()
        parent = self.parent()
        if hasattr(parent, "game_id_edit"):
            parent.game_id_edit.setText(game_id)
            if hasattr(parent, "load_steam_game_stats"):
                parent.load_steam_game_stats()
        self.accept()

    @staticmethod
    def parse_stats_file(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            m = re.search(r"UserGameStatsSchema_(\d+)\.bin", os.path.basename(path))
            game_id = m.group(1) if m else "?"
            version = "?"
            v_match = re.search(rb"version\x00([0-9.]+)\x00", data)
            if v_match:
                version = v_match.group(1).decode(errors="ignore")
            return version, game_id
        except Exception:
            return "?", "?"
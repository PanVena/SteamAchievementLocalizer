from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QLineEdit, QSizePolicy, QSpacerItem, QCheckBox
from PyQt6.QtCore import Qt
import os
import re
from plugins.highlight_delegate import HighlightDelegate

class NumericTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem that sorts numerically instead of alphabetically"""
    def __init__(self, text, numeric_value):
        super().__init__(text)
        self.numeric_value = numeric_value
    
    def __lt__(self, other):
        """Override less-than operator for sorting"""
        if isinstance(other, NumericTableWidgetItem):
            return self.numeric_value < other.numeric_value
        return super().__lt__(other)

class UserGameStatsListDialog(QDialog):
    def __init__(self, parent, stats_list, steam_game_names=None, settings=None):
        super().__init__(parent)
        self.steam_game_names = steam_game_names or {}
        self.settings = settings
        translations = getattr(self.parent(), "translations", {})
        self.setWindowTitle(parent.translations.get("user_game_stats_list"))
        self.setMinimumSize(720, 600)
        layout = QVBoxLayout()

        # --- Steam API name toggle with hint ---
        from PyQt6.QtWidgets import QCheckBox
        toggle_layout = QVBoxLayout()
        self.use_steam_name_checkbox = QCheckBox(translations.get("use_steam_name", "Use Steam API Name"))
        if self.settings:
            self.use_steam_name_checkbox.setChecked(self.settings.value("UseSteamName", False, type=bool))
        self.use_steam_name_checkbox.stateChanged.connect(self.on_steam_name_toggle)
        
        hint_label = QLabel(translations.get("use_steam_name_hint", "If you can't find your game - check this option"))
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: gray; font-size: 10px;")
        
        toggle_layout.addWidget(self.use_steam_name_checkbox)
        toggle_layout.addWidget(hint_label)
        layout.addLayout(toggle_layout)

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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            translations.get("gamename_list"),
            translations.get("version"),
            translations.get("game_id"),
            translations.get("achievements_count")
        ])
        # Enable sorting
        self.table.setSortingEnabled(True)
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
        # Disable sorting while filling to avoid performance issues
        self.table.setSortingEnabled(False)
        
        self.table.setRowCount(len(stats_list))
        for row, (gamename, version, game_id, achievement_count) in enumerate(stats_list):

            # Version column with numeric sorting
            try:
                version_num = int(version) if version != "?" else -1
            except (ValueError, TypeError):
                version_num = -1
            item_version = NumericTableWidgetItem(str(version), version_num)
            item_version.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, item_version)

            # Game name column (text sorting is fine)
            self.table.setItem(row, 0, QTableWidgetItem(str(gamename)))

            # Game ID column with numeric sorting
            try:
                game_id_num = int(game_id) if game_id != "?" else -1
            except (ValueError, TypeError):
                game_id_num = -1
            item_id = NumericTableWidgetItem(str(game_id), game_id_num)
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_id)

            # Achievement count column with numeric sorting
            try:
                ach_count_num = int(achievement_count) if achievement_count != "?" else -1
            except (ValueError, TypeError):
                ach_count_num = -1
            item_ach = NumericTableWidgetItem(str(achievement_count), ach_count_num)
            item_ach.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, item_ach)
        
        # Re-enable sorting after filling
        self.table.setSortingEnabled(True)
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
            if i in (2, 3):
                header.setSectionResizeMode(i, self.table.horizontalHeader().ResizeMode.Interactive)
                self.table.setColumnWidth(i, 100)
            elif i == 1:
                header.setSectionResizeMode(i, self.table.horizontalHeader().ResizeMode.Interactive)
                self.table.setColumnWidth(i, 130)
            else:
                header.setSectionResizeMode(i, self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.viewport().update()
     
    def on_table_cell_clicked(self, row, col):
        self.table.selectRow(row)
        gamename = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        self.selected_gamename_label.setText(gamename)
        self.selected_row = row
        self.select_btn.setEnabled(True)

    def select_game(self):
        if self.selected_row is None:
            return
        item_id = self.table.item(self.selected_row, 2)
        if not item_id:
            return
        game_id = item_id.text()
        parent = self.parent()
        if hasattr(parent, "game_id_edit"):
            parent.game_id_edit.setText(game_id)
            # Reset force_manual_path on parent to ensure we use Steam path
            if hasattr(parent, "force_manual_path"):
                parent.force_manual_path = False
            if hasattr(parent, "load_steam_game_stats"):
                parent.load_steam_game_stats()
        self.accept()
    
    def on_steam_name_toggle(self, checked):
        """Handle Steam API name toggle - save setting and notify parent to refresh"""
        if self.settings:
            self.settings.setValue("UseSteamName", bool(checked))
        # Notify parent to refresh the dialog
        parent = self.parent()
        if hasattr(parent, "show_user_game_stats_list"):
            self.accept()  # Close current dialog
            parent.show_user_game_stats_list()  # Reopen with updated names

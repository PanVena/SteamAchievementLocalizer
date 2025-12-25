from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QHBoxLayout, QLineEdit, QSizePolicy, QSpacerItem, QCheckBox
from PyQt6.QtCore import Qt
import os
import re
import sys
import glob
import webbrowser
import subprocess
from plugins import HighlightDelegate
try:
    import requests
except ImportError:
    requests = None


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

        # --- Fetch missing names button ---
        button_layout = QHBoxLayout()
        self.fetch_names_btn = QPushButton(translations.get("fetch_missing_names", "Fetch Missing Names from Steam API"))
        self.fetch_names_btn.setToolTip(translations.get("tooltip_fetch_missing_names", ""))
        self.fetch_names_btn.clicked.connect(self.fetch_missing_names)
        
        hint_label = QLabel(translations.get("fetch_missing_names_hint", "Click to fetch game names from Steam API for all games showing 'UNKNOWN'."))
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet("color: gray; font-size: 10px;")
        
        button_layout.addWidget(self.fetch_names_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addWidget(hint_label)

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
        
        # Get achievements button (left side)
        self.select_btn = QPushButton(translations.get("get_ach"))
        self.select_btn.setEnabled(False)
        self.select_btn.setDefault(True)
        self.select_btn.setAutoDefault(True)
        # Make the button stand out (accent color depending on theme, but generally highlighted)
        self.select_btn.setStyleSheet("padding: 5px;")
        self.select_btn.clicked.connect(self.select_game)
        btn_box.addWidget(self.select_btn)

        self.selected_gamename_label = QLabel("")
        self.selected_gamename_label.setWordWrap(True)
        self.selected_gamename_label.setMinimumWidth(350)  
        btn_box.addWidget(self.selected_gamename_label)
        btn_box.addStretch(1)
        
        # Open in Steam Store button (right side)
        self.open_steam_store_btn = QPushButton(translations.get("open_in_steam_store", "Open in Steam Store"))
        self.open_steam_store_btn.setEnabled(False)
        self.open_steam_store_btn.setToolTip(translations.get("tooltip_open_in_steam_store", ""))
        self.open_steam_store_btn.clicked.connect(self.open_in_steam_store)
        btn_box.addWidget(self.open_steam_store_btn)
        
        # Open in File Manager button (right side)
        self.open_file_manager_btn = QPushButton(translations.get("open_in_file_manager", "Open in File Manager"))
        self.open_file_manager_btn.setEnabled(False)
        self.open_file_manager_btn.setToolTip(translations.get("tooltip_open_in_file_manager", ""))
        self.open_file_manager_btn.clicked.connect(self.open_in_file_manager)
        btn_box.addWidget(self.open_file_manager_btn)

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
        self.open_steam_store_btn.setEnabled(False)
        self.open_file_manager_btn.setEnabled(False)
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
        self.open_steam_store_btn.setEnabled(True)
        self.open_file_manager_btn.setEnabled(True)


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
    
    
    def fetch_missing_names(self):
        """Fetch missing game names from Steam API for all unknown games"""
        parent = self.parent()
        if not hasattr(parent, 'get_steam_game_name'):
            return
        
        # Get unknown text
        unknown_text = parent.translations.get("unknown", "Unknown")
        
        # Collect games to fetch (Unknown or code names marked with *)
        games_to_fetch = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            id_item = self.table.item(row, 2)
            if name_item and id_item:
                name = name_item.text()
                # Fetch if Unknown or starts with * (code name from binary)
                if name == unknown_text or name.startswith("*"):
                    games_to_fetch.append((row, id_item.text()))
        
        if not games_to_fetch:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                parent.translations.get("info", "Info"),
                parent.translations.get("fetch_complete", "Fetching complete. {count} names updated.").format(count=0)
            )
            return
        
        # Disable button and show progress
        self.fetch_names_btn.setEnabled(False)
        original_text = self.fetch_names_btn.text()
        
        # Show progress using parent's progress bar
        if hasattr(parent, 'show_progress'):
            parent.show_progress(
                parent.translations.get("fetching_names_progress", "Fetching game names..."),
                total=len(games_to_fetch)
            )
        
        # Track errors
        updated_count = 0
        error_count = 0
        rate_limited = False
        
        # Fetch names for unknown games with delay between requests
        for i, (row, game_id) in enumerate(games_to_fetch):
            # Update progress
            if hasattr(parent, 'update_progress'):
                parent.update_progress(
                    increment=1,
                    message=parent.translations.get("processing", "Processing {game_id}").format(game_id=game_id)
                )
            
            # Add delay between requests to avoid rate limiting (except for first request)
            if i > 0:
                import time
                time.sleep(0.5)  # 500ms delay between requests
            
            # Fetch from Steam API
            name = parent.get_steam_game_name(game_id, show_progress=False)
            if name and name != unknown_text:
                # Update table
                self.table.item(row, 0).setText(name)
                updated_count += 1
                # Also update stats_list for filtering
                for j, stat in enumerate(self.stats_list):
                    if stat[2] == game_id:  # Match by game_id
                        self.stats_list[j] = (name, stat[1], stat[2], stat[3])
                        break
            else:
                error_count += 1
                # Check if we hit rate limit
                if hasattr(parent, 'get_game_name_from_cache'):
                    cached = parent.get_game_name_from_cache(game_id)
                    if cached == "RATE_LIMITED":
                        rate_limited = True
                        print(f"[Fetch] Rate limited at game {i+1}/{len(games_to_fetch)}, stopping...")
                        break
        
        # Hide progress
        if hasattr(parent, 'hide_progress'):
            parent.hide_progress()
        
        # Re-enable button
        self.fetch_names_btn.setEnabled(True)
        self.fetch_names_btn.setText(original_text)
        
        # Show completion message with details
        from PyQt6.QtWidgets import QMessageBox
        if rate_limited:
            message = parent.translations.get("fetch_complete", "Fetching complete. {count} names updated.").format(count=updated_count)
            # Use format for localized string insertion
            rate_limit_msg = parent.translations.get("fetch_rate_limited", "\n\n⚠️ Rate limited by Steam after {count} requests. Try again later for remaining games.").format(count=i+1)
            message += rate_limit_msg
        elif error_count > 0:
            message = parent.translations.get("fetch_complete", "Fetching complete. {count} names updated.").format(count=updated_count)
            # Use format for localized string insertion
            error_msg = parent.translations.get("fetch_error_count", "\n\n{count} games could not be fetched (errors logged to console).").format(count=error_count)
            message += error_msg
        else:
            message = parent.translations.get("fetch_complete", "Fetching complete. {count} names updated.").format(count=updated_count)
        
        QMessageBox.information(
            self,
            parent.translations.get("success", "Success"),
            message
        )
    
    def open_in_steam_store(self):
        """Open the selected game's Steam Store page in the default browser"""
        if self.selected_row is None:
            return
        item_id = self.table.item(self.selected_row, 2)
        if not item_id:
            return
        game_id = item_id.text()
        
        # Open Steam Store page in browser
        steam_url = f"https://store.steampowered.com/app/{game_id}/"
        webbrowser.open(steam_url)
    
    def open_in_file_manager(self):
        """Open the achievements file folder in the file manager"""
        if self.selected_row is None:
            return
        item_id = self.table.item(self.selected_row, 2)
        if not item_id:
            return
        game_id = item_id.text()
        
        # Get the parent window to access steam folder path and steam_integration
        parent = self.parent()
        if not hasattr(parent, 'steam_folder') or not hasattr(parent, 'steam_integration'):
            return
        
        # Construct the path to the stats file
        stats_folder = os.path.join(parent.steam_folder, "appcache", "stats")
        
        # Find the actual file for this game
        pattern = os.path.join(stats_folder, f"UserGameStatsSchema_{game_id}.bin")
        files = glob.glob(pattern)
        
        if files and os.path.isfile(files[0]):
            # Use existing steam_integration method to open file in explorer
            parent.steam_integration.open_file_in_explorer(files[0])
        elif os.path.exists(stats_folder):
            # If file not found, just open the stats folder
            if sys.platform == "win32":
                os.startfile(stats_folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", stats_folder])
            else:  # Linux
                env = os.environ.copy()
                if "LD_LIBRARY_PATH" in env:
                    del env["LD_LIBRARY_PATH"]
                subprocess.Popen(["xdg-open", stats_folder], env=env)




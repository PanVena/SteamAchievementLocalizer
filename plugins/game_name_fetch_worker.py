import os
import re
from PyQt6.QtCore import QThread, pyqtSignal

class GameNameFetchWorker(QThread):
    """Worker thread for fetching game names from Steam API in background"""
    progress = pyqtSignal(int, int, str)  # (current, total, message)
    finished = pyqtSignal(list)      # result list
    api_error = pyqtSignal(str)      # error message
    
    def __init__(self, stats_files, stats_dir, gui):
        super().__init__()
        self.stats_files = stats_files
        self.stats_dir = stats_dir
        self.gui = gui
        self._is_cancelled = False
        
    def run(self):
        stats_list = []
        use_steam_api = self.gui.settings.value("UseSteamName", False, type=bool)
        
        valid_files = [f for f in self.stats_files if re.match(r"UserGameStatsSchema_(\d+)\.bin", f)]
        total = len(valid_files)
        consecutive_failures = 0
        
        for i, fname in enumerate(valid_files):
            if self._is_cancelled:
                break
                
            m = re.match(r"UserGameStatsSchema_(\d+)\.bin", fname)
            game_id = m.group(1)
            file_path = os.path.join(self.stats_dir, fname)
            
            try:
                # Read file once for all metadata
                with open(file_path, "rb") as f:
                    file_data = f.read()
                
                # Use BinaryParser for version and achievement count
                achievement_count = self.gui.binary_parser.get_achievement_count(file_data)
                version = self.gui.binary_parser.get_version(file_data)
                
                # Use centralized game name fetching procedure
                gamename = self.gui.get_game_name_for_id(game_id, raw_data=file_data, show_progress=False)
                
                stats_list.append((
                    gamename,
                    str(version) if version is not None else self.gui.translations.get("unknown"),
                    game_id,
                    achievement_count
                ))
                self.progress.emit(i + 1, total, self.gui.translations.get("processing", "Processing {game_id}...").format(game_id=game_id))
            except Exception:
                self.progress.emit(i + 1, total, self.gui.translations.get("processing", "Processing {game_id}...").format(game_id=game_id))
                
        if not self._is_cancelled:
            self.finished.emit(stats_list)

    def cancel(self):
        self._is_cancelled = True

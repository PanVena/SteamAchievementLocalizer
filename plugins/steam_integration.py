"""
Steam Integration Plugin for Steam Achievement Localizer
Handles Steam path detection, game ID parsing, and Steam-related operations
"""
import os
import re
import sys
import subprocess
import shutil
from typing import Optional, List, Tuple

if sys.platform == "win32":
    import winreg


class SteamIntegration:
    """Handles Steam-related functionality"""
    
    def __init__(self):
        self.steam_path: Optional[str] = None
    
    def detect_steam_path(self) -> Optional[str]:
        """Auto-detect Steam installation path"""
        home = os.path.expanduser("~")
        
        # Linux/Mac paths
        possible_paths = [
            # macOS standard paths
            os.path.join(home, "Library", "Application Support", "Steam"),
            os.path.join(home, "Library", "Application Support", "steam"),
            # Standard Linux paths
            os.path.join(home, ".steam", "steam"),
            os.path.join(home, ".steam", "Steam"),
            os.path.join(home, ".local", "share", "Steam"),
            os.path.join(home, ".local", "share", "steam"),
            os.path.join(home, ".steam", "root"),
            os.path.join(home, ".steam", "Root"),
            # Flatpak Steam version
            os.path.join(home, ".var", "app", "com.valvesoftware.Steam", ".local", "share", "Steam"),
            # Snap Steam version
            os.path.join(home, "snap", "steam", "common", ".local", "share", "Steam"),
            os.path.join(home, "snap", "steam", "common", ".steam", "steam"),
            os.path.join(home, "snap", "steam", "common", ".steam", "Steam"),
            os.path.join(home, "snap", "steam", "common", ".steam", "root"),
            os.path.join(home, "snap", "steam", "common", ".steam", "Root"),
        ]
        
        # Windows detection
        if sys.platform == "win32":
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam") as key:
                    steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                    steam_path = os.path.realpath(steam_path)
                    if os.path.exists(steam_path):
                        self.steam_path = steam_path
                        return steam_path
            except Exception:
                fallback = "C:\\Program Files (x86)\\Steam"
                if os.path.exists(fallback):
                    self.steam_path = fallback
                    return fallback
        else:
            # Unix-like systems
            for path in possible_paths:
                if os.path.exists(path):
                    self.steam_path = path
                    return path
        
        return None
    
    def parse_game_id(self, text: str) -> Optional[str]:
        """Extract game ID from text (URL or plain ID)"""
        text = text.strip()
        
        # Extract ID from Steam URL
        match = re.search(r'/app/(\d+)', text)
        if match:
            return match.group(1)
        
        # If only digits, return as is
        if text.isdigit():
            return text
        
        return None
    
    def get_stats_file_path(self, steam_path: str, game_id: str) -> str:
        """Get path to UserGameStatsSchema file"""
        return os.path.abspath(
            os.path.join(
                steam_path, "appcache", "stats",
                f"UserGameStatsSchema_{game_id}.bin"
            )
        )
    
    def get_stats_files_list(self, steam_path: str) -> List[Tuple[str, str, str]]:
        """Get list of all stats files with basic info"""
        stats_dir = os.path.join(steam_path, "appcache", "stats")
        
        if not os.path.isdir(stats_dir):
            return []
        
        stats_files = [
            f for f in os.listdir(stats_dir) 
            if f.startswith("UserGameStatsSchema_") and f.endswith(".bin")
        ]
        
        stats_list = []
        for fname in stats_files:
            match = re.match(r"UserGameStatsSchema_(\d+)\.bin", fname)
            game_id = match.group(1) if match else "?"
            file_path = os.path.join(stats_dir, fname)
            
            try:
                # Get basic file info
                file_size = os.path.getsize(file_path)
                stats_list.append((fname, game_id, str(file_size)))
            except Exception:
                stats_list.append((fname, game_id, "?"))
        
        return stats_list
    
    def open_file_in_explorer(self, filepath: str) -> bool:
        """Open file in system file explorer"""
        if not os.path.isfile(filepath):
            return False
        
        folder = os.path.dirname(filepath)
        
        try:
            if sys.platform == "win32":
                subprocess.run(f'explorer /select,"{filepath}"', shell=True)
                return True
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", filepath])
                return True
            else:
                # Linux - try various file managers
                candidates = [
                    ["nautilus", "--select", filepath],
                    ["dolphin", "--select", filepath],
                    ["thunar", "--select", filepath],
                    ["nemo", "--browser", "--select", filepath]
                ]
                
                # Prepare environment without LD_LIBRARY_PATH for Nuitka/PyInstaller compatibility
                env = os.environ.copy()
                if "LD_LIBRARY_PATH" in env:
                    del env["LD_LIBRARY_PATH"]
                
                for cmd in candidates:
                    if shutil.which(cmd[0]):
                        try:
                            subprocess.run(cmd, check=True, env=env)
                            return True
                        except Exception:
                            continue
                
                # Fallback - just open folder
                try:
                    subprocess.run(["xdg-open", folder], env=env)
                    return True
                except Exception:
                    pass
        except Exception:
            pass
        
        return False
    
    def validate_steam_path(self, path: str) -> bool:
        """Check if the given path is a valid Steam installation"""
        if not path or not os.path.exists(path):
            return False
        
        # Check for key Steam directories/files
        steam_indicators = [
            "appcache",
            "steamapps",
            "config",
        ]
        
        for indicator in steam_indicators:
            if os.path.exists(os.path.join(path, indicator)):
                return True
        
        return False
    
    def get_steam_userdata_paths(self, steam_path: str) -> List[str]:
        """Get list of Steam user data directories"""
        userdata_path = os.path.join(steam_path, "userdata")
        
        if not os.path.exists(userdata_path):
            return []
        
        user_dirs = []
        for item in os.listdir(userdata_path):
            item_path = os.path.join(userdata_path, item)
            if os.path.isdir(item_path) and item.isdigit():
                user_dirs.append(item_path)
        
        return user_dirs
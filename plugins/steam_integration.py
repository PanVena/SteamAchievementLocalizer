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
                subprocess.Popen(f'explorer /select,"{filepath}"', shell=True)
                return True
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", filepath])
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
                            # Use Popen instead of run to avoid blocking
                            subprocess.Popen(cmd, env=env)
                            return True
                        except Exception:
                            continue
                
                # Fallback - just open folder
                try:
                    subprocess.Popen(["xdg-open", folder], env=env)
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

    def is_steam_running(self) -> bool:
        """Check if Steam is currently running"""
        try:
            if sys.platform == "win32":
                try:
                    output = subprocess.check_output('tasklist /FI "IMAGENAME eq steam.exe" /NH', shell=True).decode()
                    return "steam.exe" in output.lower()
                except Exception:
                    pass
            else:
                # Linux/macOS
                process_name = "Steam" if sys.platform == "darwin" else "steam"
                try:
                    return subprocess.call(["pgrep", "-x", process_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
                except FileNotFoundError:
                    try:
                        return subprocess.call(["pidof", process_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
                    except Exception:
                        pass
        except Exception:
            pass
        return False

    def restart_steam(self) -> bool:
        """
        Restarts the Steam client.
        If Steam is not currently running, it just starts it.
        Returns True if the restart command was successfully initiated.
        """
        import time

        try:
            is_running = self.is_steam_running()
            
            if sys.platform == "win32":
                if is_running:
                    # Shutdown Steam
                    subprocess.run(["start", "steam://exit"], shell=True)
                    
                    # Wait for it to close (max 10 seconds)
                    for _ in range(20):
                        time.sleep(0.5)
                        if not self.is_steam_running():
                            break
                
                # Launch Steam
                steam_path = self.steam_path
                if not steam_path:
                    steam_path = self.detect_steam_path()
                
                steam_exe = os.path.join(steam_path, "steam.exe") if steam_path else "steam"
                subprocess.Popen([steam_exe])
                return True
                
            elif sys.platform == "darwin":
                if is_running:
                    # macOS
                    subprocess.run(["osascript", "-e", 'quit app "Steam"'])
                    time.sleep(3)
                
                subprocess.run(["open", "-a", "Steam"])
                return True
                
            else:
                # Linux
                if is_running:
                    # Try graceful shutdown first
                    subprocess.run(["steam", "-shutdown"], check=False)
                    
                    # Give it time to close
                    time.sleep(3)
                
                # Start in background
                subprocess.Popen(["steam"], start_new_session=True, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
                
        except Exception as e:
            print(f"Failed to restart Steam: {e}")
            return False
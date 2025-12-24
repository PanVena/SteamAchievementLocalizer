"""
Icon Loader Plugin for Steam Achievement Localizer
Handles downloading and caching achievement icons
"""
import os
import requests
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QSettings, QStandardPaths
from typing import Optional


class IconLoader:
    """Handles loading and caching of achievement icons"""
    
    def __init__(self, settings: QSettings):
        self.settings = settings
        # Use app data directory for icon cache
        cache_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
        self.cache_dir = os.path.join(cache_dir, "achievement_icons")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_cache_path(self, icon_hash: str) -> str:
        """Get local cache path for an icon hash"""
        # Remove .jpg extension if present
        icon_hash = icon_hash.replace('.jpg', '').replace('.png', '')
        return os.path.join(self.cache_dir, f"{icon_hash}.jpg")
    
    def get_steam_icon_url(self, icon_hash: str, app_id: str = None) -> str:
        """
        Construct full Steam CDN URL from icon hash
        
        Args:
            icon_hash: Icon file hash (e.g., 'a952fd4c9f0dc54dfb11a8860f3a61e851438532.jpg')
            app_id: App ID for constructing URL (required for correct URL)
            
        Returns:
            Full URL to icon on Steam CDN
        """
        # Remove extension if present
        icon_hash = icon_hash.replace('.jpg', '').replace('.png', '')
        
        # Steam CDN URL format: http://media.steampowered.com/steamcommunity/public/images/apps/{app_id}/{hash}.jpg
        # If no app_id provided, use generic CDN (may not work for all icons)
        if app_id:
            return f"http://media.steampowered.com/steamcommunity/public/images/apps/{app_id}/{icon_hash}.jpg"
        else:
            # Fallback to cloudflare CDN (may not have all icons)
            return f"https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/{icon_hash}.jpg"
    
    def load_icon(self, icon_hash: str, app_id: str = None, size: tuple = (48, 48)) -> Optional[QPixmap]:
        """
        Load icon from cache or download if not cached
        
        Args:
            icon_hash: Icon file hash from binary (e.g., 'a952fd4c9f0dc54dfb11a8860f3a61e851438532.jpg')
            app_id: Optional app ID (not currently used but kept for future)
            size: Desired icon size (width, height)
            
        Returns:
            QPixmap with the icon, or None if failed
        """
        if not icon_hash:
            return None
        
        # Construct full URL
        icon_url = self.get_steam_icon_url(icon_hash, app_id)
        cache_path = self.get_cache_path(icon_hash)
        
        # Try to load from cache first
        if os.path.exists(cache_path):
            pixmap = QPixmap(cache_path)
            if not pixmap.isNull():
                return pixmap.scaled(size[0], size[1])
        
        # Download icon
        try:
            response = requests.get(icon_url, timeout=2)  # Reduced timeout to prevent blocking
            response.raise_for_status()
            
            # Save to cache
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            # Load and return
            pixmap = QPixmap(cache_path)
            if not pixmap.isNull():
                return pixmap.scaled(size[0], size[1])
                
        except Exception as e:
            print(f"[IconLoader] Failed to load icon {icon_hash}: {e}")
            return None
        
        return None
    
    def get_placeholder_icon(self, size: tuple = (48, 48)) -> QPixmap:
        """Get a placeholder icon for missing/failed icons"""
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(0x808080)  # Gray color
        return pixmap
    
    def clear_cache(self):
        """Clear all cached icons"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)

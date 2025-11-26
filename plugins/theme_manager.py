import os
import json
import subprocess
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QGroupBox, QPushButton, QComboBox, QCheckBox, QTableWidget


class ThemeManager:
    """Plugin for managing themes and fonts"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.settings = QSettings("Vena", "Steam Achievement Localizer")
        self.themes_dir = "assets/themes"
        
        # Store original system palette for restoration
        app = QApplication.instance()
        if app:
            self.original_system_palette = app.palette()
        else:
            self.original_system_palette = None
        
        self.available_themes = self._load_available_themes()
    
    def _load_available_themes(self):
        """Load list of available themes"""
        themes = {}
        if os.path.exists(self.themes_dir):
            for filename in os.listdir(self.themes_dir):
                if filename.endswith('.json'):
                    theme_path = os.path.join(self.themes_dir, filename)
                    try:
                        with open(theme_path, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                            # Use the 'name' from JSON as the key
                            theme_name = theme_data.get('name')
                            if theme_name:
                                themes[theme_name] = theme_data
                            else:
                                # Fallback to filename if no name in JSON
                                theme_name = filename[:-5].capitalize()
                                themes[theme_name] = theme_data
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        print(f"Error loading theme from {filename}: {e}")
        return themes
    
    def get_available_theme_names(self):
        """Get list of available theme names sorted by priority and name"""
        themes_list = []
        
        for theme_name, theme_data in self.available_themes.items():
            priority = theme_data.get('priority', 999)  # Default priority for themes without it
            themes_list.append((priority, theme_name))
        
        # Sort by priority (ascending), then by name (alphabetically)
        themes_list.sort(key=lambda x: (x[0], x[1]))
        
        return [theme_name for priority, theme_name in themes_list]
    
    def get_theme_display_name(self, theme_name, language_code='en'):
        """Get localized display name for theme"""
        if theme_name not in self.available_themes:
            return theme_name
            
        theme_data = self.available_themes[theme_name]
        
        # Try to get display name in requested language
        display_names = theme_data.get('display_names', {})
        if display_names:
            # Try requested language, fallback to English, then to theme name
            return display_names.get(language_code, 
                                    display_names.get('en', theme_name))
        
        # Fallback to theme name if no display_names
        return theme_name
    
    def apply_palette_from_config(self, app, palette_config):
        """Apply palette from configuration"""
        if palette_config == "system":
            # Use original system palette if available, otherwise current style palette
            if self.original_system_palette:
                palette = QPalette(self.original_system_palette)
            else:
                palette = app.style().standardPalette()
            
            # Check accent color mode for current theme
            accent_mode = self.get_current_accent_color_mode()
            
            if accent_mode == "custom":
                # Use custom accent color
                custom_color = self.get_custom_accent_color()
                if custom_color:
                    palette.setColor(QPalette.ColorRole.Highlight, custom_color)
                    palette.setColor(QPalette.ColorRole.Link, custom_color)
                    # Adjust highlighted text color for better contrast
                    if custom_color.lightness() < 128:
                        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
                    else:
                        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
            # For "theme_default" mode with system theme, keep original system colors
            # This preserves the original system accent color
            
            app.setPalette(palette)
            return
            
        palette = QPalette()
        
        # Apply colors from configuration
        color_mappings = {
            'window': QPalette.ColorRole.Window,
            'window_text': QPalette.ColorRole.WindowText,
            'base': QPalette.ColorRole.Base,
            'alternate_base': QPalette.ColorRole.AlternateBase,
            'tooltip_base': QPalette.ColorRole.ToolTipBase,
            'tooltip_text': QPalette.ColorRole.ToolTipText,
            'text': QPalette.ColorRole.Text,
            'button': QPalette.ColorRole.Button,
            'button_text': QPalette.ColorRole.ButtonText,
            'bright_text': QPalette.ColorRole.BrightText,
            'link': QPalette.ColorRole.Link,
            'highlight': QPalette.ColorRole.Highlight,
            'highlighted_text': QPalette.ColorRole.HighlightedText
        }
        
        for config_key, qt_role in color_mappings.items():
            if config_key in palette_config:
                color_value = palette_config[config_key]
                
                # Handle "system" value - use system color
                if color_value == "system" and config_key in ['highlight', 'link']:
                    if self.original_system_palette:
                        system_color = self.original_system_palette.color(qt_role)
                        palette.setColor(qt_role, system_color)
                    continue
                
                if isinstance(color_value, list) and len(color_value) >= 3:
                    # RGB values
                    color = QColor(color_value[0], color_value[1], color_value[2])
                elif isinstance(color_value, str):
                    # Color name or hex
                    if color_value == "white":
                        color = QColor(255, 255, 255)
                    elif color_value == "red":
                        color = QColor(255, 0, 0)
                    else:
                        color = QColor(color_value)
                else:
                    continue
                palette.setColor(qt_role, color)
        
        # Override accent colors based on current theme settings
        accent_mode = self.get_current_accent_color_mode()
        
        if accent_mode == "custom":
            # Use custom accent color
            custom_color = self.get_custom_accent_color()
            if custom_color:
                palette.setColor(QPalette.ColorRole.Highlight, custom_color)
                palette.setColor(QPalette.ColorRole.Link, custom_color)
                # Adjust highlighted text color for better contrast
                if custom_color.lightness() < 128:
                    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
                else:
                    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        # For "theme_default" mode, use colors from theme config (already applied above)
        
        app.setPalette(palette)
    
    def _apply_dark_palette(self, app):
        """Apply dark palette (for system theme)"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 20))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(dark_palette)
    
    def get_system_accent_color(self):
        """Get system accent color"""
        try:
            # Try to get GTK/GNOME accent color first
            try:
                # Try newer GNOME setting first
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "accent-color"], 
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    accent_name = result.stdout.strip().strip("'\"")
                    # Map GNOME accent color names to actual colors
                    gnome_accent_colors = {
                        'blue': QColor(52, 132, 228),
                        'teal': QColor(26, 188, 156),
                        'green': QColor(46, 194, 126),
                        'yellow': QColor(248, 228, 92),
                        'orange': QColor(255, 120, 0),
                        'red': QColor(237, 51, 59),
                        'pink': QColor(224, 27, 116),
                        'purple': QColor(154, 78, 174),
                        'slate': QColor(99, 109, 125)
                    }
                    if accent_name in gnome_accent_colors:
                        return gnome_accent_colors[accent_name]
                
                # Try older GTK theme name approach
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"], 
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    theme_name = result.stdout.strip().strip("'\"").lower()
                    if 'adwaita' in theme_name:
                        # Try to get selected color from GTK theme
                        result = subprocess.run(
                            ["gsettings", "get", "org.gnome.desktop.wm.preferences", "theme"], 
                            capture_output=True, text=True, timeout=2
                        )
                        
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                pass

            # Try KDE accent color (works better with latest Plasma)
            try:
                # Try KDE6 first
                result = subprocess.run(
                    ["kreadconfig6", "--group", "Colors:Selection", "--key", "BackgroundNormal"], 
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode != 0:
                    # Fallback to KDE5
                    result = subprocess.run(
                        ["kreadconfig5", "--group", "Colors:Selection", "--key", "BackgroundNormal"], 
                        capture_output=True, text=True, timeout=2
                    )
                
                if result.returncode == 0 and result.stdout.strip():
                    color_str = result.stdout.strip()
                    # Parse KDE color format (r,g,b)
                    if ',' in color_str:
                        rgb = [int(x.strip()) for x in color_str.split(',')]
                        if len(rgb) >= 3:
                            return QColor(rgb[0], rgb[1], rgb[2])
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                pass

            # Try to get system highlight color from current application
            app = QApplication.instance()
            if app:
                # Get system palette
                system_palette = app.style().standardPalette()
                highlight_color = system_palette.color(QPalette.ColorRole.Highlight)
                
                # Check if it's not the default Qt blue (#308cc6 or similar)
                if highlight_color.name().lower() not in ['#308cc6', '#0078d4', '#007acc']:
                    return highlight_color

        except Exception:
            pass

        # Ultimate fallback: return None to use system default
        return None

    def get_theme_default_accent_color(self, theme_name=None):
        """Get default accent color from theme configuration"""
        if theme_name is None:
            theme_name = self.get_current_theme()
            
        if theme_name not in self.available_themes:
            return None
            
        theme_config = self.available_themes[theme_name]
        palette_config = theme_config.get("palette")
        
        if not palette_config or palette_config == "system":
            return None
            
        # Try to get highlight color from theme palette
        if "highlight" in palette_config:
            color_value = palette_config["highlight"]
            
            # Handle "system" value - return original system accent color
            if color_value == "system":
                if self.original_system_palette:
                    return self.original_system_palette.color(QPalette.ColorRole.Highlight)
                else:
                    return self.get_system_accent_color()
                
            if isinstance(color_value, list) and len(color_value) >= 3:
                return QColor(color_value[0], color_value[1], color_value[2])
            elif isinstance(color_value, str):
                if color_value == "white":
                    return QColor(255, 255, 255)
                elif color_value == "red":
                    return QColor(255, 0, 0)
                else:
                    return QColor(color_value)
        
        # Fallback to link color if highlight is not available
        if "link" in palette_config:
            color_value = palette_config["link"]
            
            # Handle "system" value for link as well
            if color_value == "system":
                if self.original_system_palette:
                    return self.original_system_palette.color(QPalette.ColorRole.Link)
                else:
                    return self.get_system_accent_color()
                
            if isinstance(color_value, list) and len(color_value) >= 3:
                return QColor(color_value[0], color_value[1], color_value[2])
            elif isinstance(color_value, str):
                if color_value == "white":
                    return QColor(255, 255, 255)
                elif color_value == "red":
                    return QColor(255, 0, 0)
                else:
                    return QColor(color_value)
        
        return None

    def is_system_dark(self):
        """Check if system theme is dark"""
        # Check GTK theme
        gtk_theme = os.environ.get("GTK_THEME", "").lower()
        if "dark" in gtk_theme:
            return True
        
        try:
            app = QApplication.instance()
            if app:
                palette = app.palette()
                window_color = palette.color(QPalette.ColorRole.Window)
                brightness = (window_color.red() + window_color.green() + window_color.blue()) / 3
                if brightness < 128:
                    return True
        except:
            pass
            
        return False
    
    def apply_styles_from_config(self, styles_config):
        """Apply styles from configuration"""
        # First clear all styles
        self._clear_all_styles()
        
        if isinstance(styles_config, dict):
            # Check if this is system theme with different styles for light/dark
            if "dark" in styles_config and "light" in styles_config:
                # System theme - use minimal styles to preserve system appearance
                if self.is_system_dark():
                    styles_to_apply = styles_config["dark"]
                else:
                    styles_to_apply = styles_config["light"]
            else:
                styles_to_apply = styles_config
            
            # Apply styles to widgets (only non-empty styles)
            for widget_type, style in styles_to_apply.items():
                if style.strip():  # Only apply non-empty styles
                    self._apply_style_to_widgets(widget_type, style)
    
    def _clear_all_styles(self):
        """Clear all custom styles"""
        widget_types = [QLabel, QLineEdit, QGroupBox, QPushButton]
        for widget_type in widget_types:
            for widget in self.main_window.findChildren(widget_type):
                widget.setStyleSheet("")
    
    def _apply_style_to_widgets(self, widget_type, style):
        """Apply style to widgets of specific type"""
        if widget_type == "QLabel":
            for widget in self.main_window.findChildren(QLabel):
                widget.setStyleSheet(style)
        elif widget_type == "QLineEdit":
            for widget in self.main_window.findChildren(QLineEdit):
                widget.setStyleSheet(style)
        elif widget_type == "QGroupBox":
            for widget in self.main_window.findChildren(QGroupBox):
                widget.setStyleSheet(style)
        elif widget_type == "QPushButton":
            for widget in self.main_window.findChildren(QPushButton):
                widget.setStyleSheet(style)
    
    def set_theme(self, theme_name):
        """Set theme"""
        if theme_name not in self.available_themes:
            print(f"Theme {theme_name} not found!")
            return
        
        theme_config = self.available_themes[theme_name]
        app = QApplication.instance()
        
        # Check if app exists
        if not app:
            print("No QApplication instance found, skipping theme application")
            # Save settings even if app is missing
            self.settings.setValue("theme", theme_name)
            self.settings.sync()
            return
        
        # Set application style
        if theme_config.get("style") == "system":
            # Use native system style
            app.setStyle(app.style().name())
        else:
            app.setStyle(theme_config.get("style", "Fusion"))
        
        # Apply palette
        palette_config = theme_config.get("palette")
        if palette_config:
            self.apply_palette_from_config(app, palette_config)
        
        # Apply styles
        styles_config = theme_config.get("styles")
        if styles_config:
            self.apply_styles_from_config(styles_config)
        
        # Save settings
        self.settings.setValue("theme", theme_name)
        self.settings.sync()
    
    def get_current_theme(self):
        """Get current theme"""
        return self.settings.value("theme", "System")
    
    def apply_font_to_widgets(self):
        """Apply font settings to all widgets"""
        font_weight = self.settings.value("font_weight", "Normal")
        font_size = int(self.settings.value("font_size", 9))
        
        font = QFont()
        font.setPointSize(font_size)
        font.setWeight(QFont.Weight.Bold if font_weight == "Bold" else QFont.Weight.Normal)
        
        # Apply font to application
        QApplication.setFont(font)
        
        # Check if main_window has setFont method
        if hasattr(self.main_window, 'setFont'):
            # Force update font for all child widgets
            self.main_window.setFont(font)
            
            # Explicitly update fonts for key widgets
            widget_types = [QLabel, QPushButton, QLineEdit, QGroupBox, QComboBox, QCheckBox]
            for widget_type in widget_types:
                for widget in self.main_window.findChildren(widget_type):
                    widget.setFont(font)
            
            # Update table font
            if hasattr(self.main_window, 'table'):
                self.main_window.table.setFont(font)
                self.main_window.table.horizontalHeader().setFont(font)
                self.main_window.table.verticalHeader().setFont(font)
            
            # Force repaint
            self.main_window.update()
    
    def set_font_weight(self, weight):
        """Set font weight"""
        self.settings.setValue("font_weight", weight)
        self.settings.sync()
        self.apply_font_to_widgets()
    
    def set_font_size(self, size):
        """Set font size"""
        self.settings.setValue("font_size", size)
        self.settings.sync()
        self.apply_font_to_widgets()
    
    def get_current_font_weight(self):
        """Get current font weight"""
        return self.settings.value("font_weight", "Normal")
    
    def get_current_font_size(self):
        """Get current font size"""
        return int(self.settings.value("font_size", 9))
    
    def set_accent_color(self, color_mode, custom_color=None):
        """Set accent color mode and custom color if applicable"""
        current_theme = self.get_current_theme()
        
        # Save settings per theme
        mode_key = f"{current_theme}_accent_mode"
        color_key = f"{current_theme}_accent_color"
        
        self.settings.setValue(mode_key, color_mode)  # "theme_default" or "custom"
        if custom_color:
            # Save color as comma-separated RGB values
            rgb_string = f"{custom_color.red()},{custom_color.green()},{custom_color.blue()}"
            self.settings.setValue(color_key, rgb_string)
        self.settings.sync()
        
        # Apply the color immediately to current theme
        self.set_theme(current_theme)  # Re-apply theme with new accent color
    
    def get_current_accent_color_mode(self):
        """Get current accent color mode for current theme"""
        current_theme = self.get_current_theme()
        mode_key = f"{current_theme}_accent_mode"
        return self.settings.value(mode_key, "theme_default")
    
    def get_custom_accent_color(self):
        """Get custom accent color for current theme"""
        current_theme = self.get_current_theme()
        color_key = f"{current_theme}_accent_color"
        color_string = self.settings.value(color_key, None)
        if color_string:
            try:
                r, g, b = map(int, color_string.split(','))
                return QColor(r, g, b)
            except (ValueError, AttributeError):
                pass
        return None
    
    def apply_custom_accent_color(self, app, custom_color):
        """Apply custom accent color to current palette"""
        if not custom_color:
            return
            
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Highlight, custom_color)
        palette.setColor(QPalette.ColorRole.Link, custom_color)
        
        # Adjust highlighted text color for better contrast
        if custom_color.lightness() < 128:
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        else:
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        
        app.setPalette(palette)
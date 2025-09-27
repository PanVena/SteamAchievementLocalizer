import os
import json
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QGroupBox, QPushButton, QComboBox, QCheckBox, QTableWidget


class ThemeManager:
    """Plugin for managing themes and fonts"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.settings = QSettings("Vena", "Steam Achievement Localizer")
        self.themes_dir = "assets/themes"
        
        # Defined theme order (System on top, then Dark/Light)
        self.theme_order = [
            "System",    # System theme - on top
            "Dark",      # Dark theme
            "Light",     # Light theme
            "Femboy"     # Femboy theme
            # Add new themes here or they will be sorted alphabetically
        ]
        
        self.available_themes = self._load_available_themes()
    
    def _load_available_themes(self):
        """Load list of available themes"""
        themes = {}
        if os.path.exists(self.themes_dir):
            for filename in os.listdir(self.themes_dir):
                if filename.endswith('.json'):
                    theme_name = filename[:-5].capitalize()  # Remove .json and capitalize
                    theme_path = os.path.join(self.themes_dir, filename)
                    try:
                        with open(theme_path, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                            themes[theme_name] = theme_data
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        print(f"Error loading theme {theme_name}: {e}")
        return themes
    
    def get_available_theme_names(self):
        """Get list of available theme names in defined order"""
        available_themes = list(self.available_themes.keys())
        
        # Sort themes according to defined order
        ordered_themes = []
        
        # First add themes from defined order
        for theme_name in self.theme_order:
            if theme_name in available_themes:
                ordered_themes.append(theme_name)
        
        # Then add all other themes alphabetically
        remaining_themes = [theme for theme in available_themes if theme not in ordered_themes]
        remaining_themes.sort()
        ordered_themes.extend(remaining_themes)
        
        return ordered_themes
    
    def add_theme_to_order(self, theme_name, position=None):
        """Add theme to defined order
        
        Args:
            theme_name (str): Theme name
            position (int, optional): Position in list. If None, adds to end
        """
        if theme_name not in self.theme_order:
            if position is None:
                self.theme_order.append(theme_name)
            else:
                self.theme_order.insert(position, theme_name)
    
    def apply_palette_from_config(self, app, palette_config):
        """Apply palette from configuration"""
        if palette_config == "system":
            # Use system palette
            if self.is_system_dark():
                self._apply_dark_palette(app)
            else:
                app.setPalette(app.style().standardPalette())
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
                # System theme
                if self.is_system_dark():
                    styles_to_apply = styles_config["dark"]
                else:
                    styles_to_apply = styles_config["light"]
            else:
                styles_to_apply = styles_config
            
            # Apply styles to widgets
            for widget_type, style in styles_to_apply.items():
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
            app.setStyle(app.style().objectName() if hasattr(app.style(), 'objectName') else 'Fusion')
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
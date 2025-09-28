"""
UI Builder Plugin for Steam Achievement Localizer
Handles UI component creation and menu building
"""
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence, QIcon
from PyQt6.QtWidgets import (
    QMenuBar, QMenu, QWidgetAction, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QGroupBox, QFrame,
    QComboBox, QMessageBox
)
from typing import Dict, List, Callable, Any, Optional


class UIBuilder:
    """Handles UI component creation and management"""
    
    def __init__(self, parent, translations: Dict[str, str]):
        self.parent = parent
        self.translations = translations
        
    def create_menubar(self) -> QMenuBar:
        """Create and return the main menu bar"""
        menubar = QMenuBar(self.parent)
        
        # File menu
        file_menu = self._create_file_menu()
        menubar.addMenu(file_menu)
        
        # Edit menu
        edit_menu = self._create_edit_menu()
        menubar.addMenu(edit_menu)
        
        # Export/Import menu
        export_import_menu = self._create_export_import_menu()
        menubar.addMenu(export_import_menu)
        
        # Save menu
        save_menu = self._create_save_menu()
        menubar.addMenu(save_menu)
        
        # Individual actions
        stats_action = self._create_stats_action()
        menubar.addAction(stats_action)

        # Language menu
        language_menu = self._create_language_menu()
        menubar.addMenu(language_menu)
        
        # Appearance menu
        appearance_menu = self._create_appearance_menu()
        menubar.addMenu(appearance_menu)
        
        about_action = self._create_about_action()
        menubar.addAction(about_action)
        
        return menubar
    
    def _create_file_menu(self) -> QMenu:
        """Create File menu"""
        file_menu = QMenu(self.translations.get("file", "File"), self.parent)
        
        # Export bin action
        export_bin_action = QAction(
            self.translations.get("export_bin", "Open bin file in explorer"), 
            self.parent
        )
        export_bin_action.triggered.connect(self.parent.export_bin)
        
        # Delete file action
        delete_file_action = QAction(
            self.translations.get("delete_stats_file", "Delete stats file"), 
            self.parent
        )
        delete_file_action.triggered.connect(self.parent.delete_current_stats_file)
        
        # Exit action
        exit_action = QAction(self.translations.get("exit", "Exit"), self.parent)
        exit_action.triggered.connect(self.parent._on_exit_action)
        
        file_menu.addAction(export_bin_action)
        file_menu.addAction(delete_file_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        return file_menu
    
    def _create_edit_menu(self) -> QMenu:
        """Create Edit menu"""
        edit_menu = QMenu(self.translations.get("edit", "Edit"), self.parent)
        
        # Global search widget
        search_widget = self._create_search_widget()
        search_action = QWidgetAction(self.parent)
        search_action.setDefaultWidget(search_widget)
        
        edit_menu.addSeparator()
        edit_menu.addAction(search_action)
        edit_menu.addSeparator()
        
        # Add standard edit actions
        if hasattr(self.parent, 'replace_in_column_action'):
            edit_menu.addAction(self.parent.replace_in_column_action)
        edit_menu.addSeparator()
        
        # Undo/Redo actions
        if hasattr(self.parent, 'undo_action'):
            edit_menu.addAction(self.parent.undo_action)
        if hasattr(self.parent, 'redo_action'):
            edit_menu.addAction(self.parent.redo_action)
        edit_menu.addSeparator()
        
        # Copy/Paste actions
        if hasattr(self.parent, 'copy_action'):
            edit_menu.addAction(self.parent.copy_action)
        if hasattr(self.parent, 'paste_action'):
            edit_menu.addAction(self.parent.paste_action)
        if hasattr(self.parent, 'cut_action'):
            edit_menu.addAction(self.parent.cut_action)
        if hasattr(self.parent, 'delete_action'):
            edit_menu.addAction(self.parent.delete_action)
        edit_menu.addSeparator()
        
        # Columns submenu
        columns_menu = self._create_columns_menu()
        edit_menu.addMenu(columns_menu)
        
        return edit_menu
    
    def _create_search_widget(self) -> QWidget:
        """Create search widget for menu"""
        if not hasattr(self.parent, 'global_search_line'):
            self.parent.global_search_line = QLineEdit()
            self.parent.global_search_line.setPlaceholderText(
                self.translations.get("in_column_search_placeholder", "Search...")
            )
            self.parent.global_search_line.setFixedWidth(200)
            if hasattr(self.parent, 'global_search_in_table'):
                self.parent.global_search_line.textChanged.connect(
                    self.parent.global_search_in_table
                )
        
        search_widget = QWidget(self.parent)
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(8, 2, 8, 2)
        search_layout.addWidget(QLabel(
            self.translations.get("in_column_search", "Search:"), 
            self.parent
        ))
        search_layout.addWidget(self.parent.global_search_line)
        
        return search_widget
    
    def _create_columns_menu(self) -> QMenu:
        """Create columns visibility submenu"""
        columns_menu = QMenu(self.translations.get("columns", "Columns"), self.parent)
        
        if hasattr(self.parent, 'headers') and self.parent.headers:
            self.parent.column_actions = {}
            
            for header in self.parent.headers:
                checkbox = QCheckBox(header)
                checkbox.setChecked(True)
                
                # Disable key columns
                if header in ["key", "ukrainian"]:
                    checkbox.setEnabled(False)
                else:
                    checkbox.toggled.connect(
                        lambda state, h=header: self.parent.set_column_visible(h, state)
                    )
                    if hasattr(self.parent, 'stretch_columns'):
                        checkbox.toggled.connect(self.parent.stretch_columns)
                
                action = QWidgetAction(self.parent)
                action.setDefaultWidget(checkbox)
                columns_menu.addAction(action)
                self.parent.column_actions[header] = checkbox
        
        return columns_menu
    
    def _create_export_import_menu(self) -> QMenu:
        """Create Export/Import menu"""
        export_import_menu = QMenu(
            self.translations.get("export_import", "Export/Import"), 
            self.parent
        )
        
        # Export all action
        export_all_action = QAction(
            self.translations.get("export_all", "Export to CSV (all languages)"), 
            self.parent
        )
        export_all_action.triggered.connect(self.parent.export_csv_all)
        
        # Export for translate action
        export_for_translate_action = QAction(
            self.translations.get("export_for_translate", "Export to CSV for translation"), 
            self.parent
        )
        export_for_translate_action.triggered.connect(self.parent.export_csv_for_translate)
        
        # Import action
        import_action = QAction(
            self.translations.get("import_csv", "Import from CSV"), 
            self.parent
        )
        import_action.triggered.connect(self.parent.import_csv)
        
        export_import_menu.addAction(export_all_action)
        export_import_menu.addAction(export_for_translate_action)
        export_import_menu.addSeparator()
        export_import_menu.addAction(import_action)
        
        return export_import_menu
    
    def _create_save_menu(self) -> QMenu:
        """Create Save menu"""
        save_menu = QMenu(self.translations.get("save", "Save"), self.parent)
        
        # Save for self action
        save_known_action = QAction(
            self.translations.get("save_bin_known", "Save bin file for yourself"), 
            self.parent
        )
        save_known_action.triggered.connect(self.parent.save_bin_know)
        
        # Save to Steam action
        save_unknown_action = QAction(
            self.translations.get("save_bin_unknown", "Save bin file to Steam folder"), 
            self.parent
        )
        save_unknown_action.triggered.connect(self.parent.save_bin_unknow)
        
        save_menu.addAction(save_known_action)
        save_menu.addAction(save_unknown_action)
        
        return save_menu
    
    def _create_language_menu(self) -> QMenu:
        """Create Language menu"""
        language_menu = QMenu(self.translations.get("language", "Language"), self.parent)
        
        # Get available locales from parent (new system)
        if hasattr(self.parent, 'available_locales') and self.parent.available_locales:
            # Use new locale system - sort locales by priority
            locale_list = []
            for name, info in self.parent.available_locales.items():
                priority = info.get('priority', 999)
                locale_list.append((priority, name, info))
            
            # Sort by priority (ascending), then by name (alphabetically)
            locale_list.sort(key=lambda x: (x[0], x[1]))
            
            for priority, lang_name, locale_info in locale_list:
                display_name = locale_info['native_name']
                
                action = QAction(display_name, self.parent)
                action.triggered.connect(
                    lambda checked, l=lang_name: self.parent.change_language(l)
                )
                language_menu.addAction(action)
        else:
            # Fallback to legacy system
            lang_files = getattr(self.parent, 'LANG_FILES', {
                "English": "assets/locales/lang_en.json",
                "Українська": "assets/locales/lang_ua.json", 
                "Polski": "assets/locales/lang_pl.json"
            })
            
            for lang in lang_files.keys():
                action = QAction(lang, self.parent)
                action.triggered.connect(
                    lambda checked, l=lang: self.parent.change_language(l)
                )
                language_menu.addAction(action)
        
        return language_menu
    
    def _create_appearance_menu(self) -> QMenu:
        """Create Appearance menu"""
        appearance_menu = QMenu(self.translations.get("appearance", "Appearance"), self.parent)
        
        # Theme submenu
        if hasattr(self.parent, 'theme_manager'):
            theme_menu = self._create_theme_submenu()
            appearance_menu.addMenu(theme_menu)
            
            # Accent color submenu
            accent_color_menu = self._create_accent_color_submenu()
            appearance_menu.addMenu(accent_color_menu)
            
            # Font weight submenu
            font_weight_menu = self._create_font_weight_submenu()
            appearance_menu.addMenu(font_weight_menu)
            
            # Font size submenu
            font_size_menu = self._create_font_size_submenu()
            appearance_menu.addMenu(font_size_menu)
        
        return appearance_menu
    
    def _create_theme_submenu(self) -> QMenu:
        """Create theme selection submenu"""
        theme_menu = QMenu(self.translations.get("theme", "Theme"), self.parent)
        theme_group = QActionGroup(self.parent)
        theme_group.setExclusive(True)
        
        self.parent.theme_actions = {}
        current_theme = self.parent.theme_manager.get_current_theme()
        
        # Get current language code for theme localization
        language_code = self._get_language_code_for_themes()
        
        available_themes = self.parent.theme_manager.get_available_theme_names()
        for theme in available_themes:
            display_name = self.parent.theme_manager.get_theme_display_name(theme, language_code)
            action = QAction(display_name, self.parent, checkable=True)
            action.setChecked(theme == current_theme)
            action.triggered.connect(
                lambda checked, t=theme: self.parent.theme_manager.set_theme(t)
            )
            
            theme_group.addAction(action)
            theme_menu.addAction(action)
            self.parent.theme_actions[theme] = action
        
        return theme_menu
    
    def _get_language_code_for_themes(self):
        """Get language code for theme localization"""
        language_map = {
            "English": "en",
            "Українська": "ua",
            "Polski": "pl"
        }
        return language_map.get(self.parent.language, "en")
    
    def _create_accent_color_submenu(self) -> QMenu:
        """Create accent color selection submenu"""
        accent_color_menu = QMenu(self.translations.get("accent_color", "Accent Color"), self.parent)
        accent_group = QActionGroup(self.parent)
        accent_group.setExclusive(True)
        
        self.parent.accent_color_actions = {}
        current_mode = self.parent.theme_manager.get_current_accent_color_mode()
        
        # Theme default accent color option
        theme_default_action = QAction(self.translations.get("theme_default", "Theme Default"), self.parent, checkable=True)
        theme_default_action.setChecked(current_mode == "theme_default")
        theme_default_action.triggered.connect(
            lambda checked: self.parent.theme_manager.set_accent_color("theme_default")
        )
        
        # Custom accent color option
        custom_action = QAction(self.translations.get("custom", "Custom..."), self.parent, checkable=True)
        custom_action.setChecked(current_mode == "custom")
        custom_action.triggered.connect(
            lambda checked: self.parent.show_accent_color_picker() if checked else None
        )
        
        accent_group.addAction(theme_default_action)
        accent_group.addAction(custom_action)
        accent_color_menu.addAction(theme_default_action)
        accent_color_menu.addAction(custom_action)
        
        self.parent.accent_color_actions["theme_default"] = theme_default_action
        self.parent.accent_color_actions["custom"] = custom_action
        
        return accent_color_menu

    def _create_font_weight_submenu(self) -> QMenu:
        """Create font weight submenu"""
        font_weight_menu = QMenu(self.translations.get("font_weight", "Font Weight"), self.parent)
        font_group = QActionGroup(self.parent)
        font_group.setExclusive(True)
        
        self.parent.font_actions = {}
        current_weight = self.parent.theme_manager.get_current_font_weight()
        
        for weight, label in [("Normal", self.translations.get("font_normal", "Normal")), 
                             ("Bold", self.translations.get("font_bold", "Bold"))]:
            action = QAction(label, self.parent, checkable=True)
            action.setChecked(weight == current_weight)
            action.triggered.connect(
                lambda checked, w=weight: self.parent.theme_manager.set_font_weight(w)
            )
            
            font_group.addAction(action)
            font_weight_menu.addAction(action)
            self.parent.font_actions[weight] = action
        
        return font_weight_menu
    
    def _create_font_size_submenu(self) -> QMenu:
        """Create font size submenu"""
        font_size_menu = QMenu(self.translations.get("font_size", "Font Size"), self.parent)
        font_size_group = QActionGroup(self.parent)
        font_size_group.setExclusive(True)
        
        self.parent.font_size_actions = {}
        current_size = self.parent.theme_manager.get_current_font_size()
        
        font_sizes = [
            (6, self.translations.get("font_xsmall", "Extra Small")),
            (8, self.translations.get("font_small", "Small")),
            (9, self.translations.get("font_standard", "Standard")),
            (10, self.translations.get("font_medium", "Medium")),
            (12, self.translations.get("font_large", "Large")),
        ]
        
        for size, label in font_sizes:
            action = QAction(label, self.parent, checkable=True)
            action.setChecked(size == current_size)
            action.triggered.connect(
                lambda checked, s=size: self.parent.theme_manager.set_font_size(s)
            )
            
            font_size_group.addAction(action)
            font_size_menu.addAction(action)
            self.parent.font_size_actions[size] = action
        
        return font_size_menu
    
    def _create_stats_action(self) -> QAction:
        """Create show stats action"""
        show_stats_action = QAction(
            self.translations.get("show_user_game_stats", "Show Game Stats"), 
            self.parent
        )
        show_stats_action.triggered.connect(self.parent.show_user_game_stats_list)
        return show_stats_action
    
    def _create_about_action(self) -> QAction:
        """Create about action"""
        about_action = QAction(self.translations.get("about", "About"), self.parent)
        about_action.triggered.connect(
            lambda: QMessageBox.information(
                self.parent,
                self.translations.get("about_app", "About App"),
                self.translations.get("about_message", "About message text")
            )
        )
        return about_action
    
    def create_file_selection_group(self) -> QGroupBox:
        """Create file selection group widget"""
        # Manual file selection
        stats_bin_path_layout = QHBoxLayout()
        
        self.parent.stats_bin_path_path = QLineEdit()
        self.parent.stats_bin_path_path.setPlaceholderText(
            self.translations.get("man_select_file_label", "Select file...")
        )
        
        self.parent.stats_bin_path_btn = QPushButton(
            self.translations.get("man_select_file", "Browse...")
        )
        self.parent.stats_bin_path_btn.clicked.connect(self.parent.stats_bin_path_search)
        
        self.parent.select_stats_bin_path_btn = QPushButton(
            self.translations.get("get_ach", "Load Achievements")
        )
        self.parent.select_stats_bin_path_btn.clicked.connect(self.parent.select_stats_bin_path)
        
        stats_bin_path_layout.addWidget(self.parent.stats_bin_path_path)
        stats_bin_path_layout.addWidget(self.parent.stats_bin_path_btn)
        stats_bin_path_layout.addWidget(self.parent.select_stats_bin_path_btn)
        
        # Create group
        stats_group = QGroupBox(
            self.translations.get("man_file_sel_label", "Manual File Selection")
        )
        stats_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_group.setLayout(stats_bin_path_layout)
        
        return stats_group
    
    def create_steam_selection_group(self) -> QGroupBox:
        """Create Steam folder and game ID selection group"""
        steam_group_layout = QVBoxLayout()
        
        # Steam folder selection
        steam_folder_layout = QHBoxLayout()
        
        self.parent.steam_folder_path = QLineEdit()
        self.parent.steam_folder_path.setPlaceholderText(
            self.translations.get("steam_folder_label", "Steam folder path...")
        )
        
        self.parent.select_steam_folder_btn = QPushButton(
            self.translations.get("select_steam_folder", "Browse Steam Folder")
        )
        self.parent.select_steam_folder_btn.clicked.connect(self.parent.select_steam_folder)
        
        steam_folder_layout.addWidget(self.parent.steam_folder_path)
        steam_folder_layout.addWidget(self.parent.select_steam_folder_btn)
        
        # Game ID selection
        game_id_layout = QHBoxLayout()
        
        self.parent.game_id_edit = QLineEdit()
        self.parent.game_id_edit.setPlaceholderText(
            self.translations.get("game_id_label", "Game ID or Steam URL...")
        )
        
        self.parent.load_game_btn = QPushButton(
            self.translations.get("get_ach", "Load Achievements")
        )
        self.parent.load_game_btn.clicked.connect(self.parent.load_steam_game_stats)
        
        self.parent.clear_game_id = QPushButton(
            self.translations.get("clear_and_paste", "Clear & Paste")
        )
        
        game_id_layout.addWidget(self.parent.game_id_edit)
        game_id_layout.addWidget(self.parent.load_game_btn)
        game_id_layout.addWidget(self.parent.clear_game_id)
        
        # Combine layouts
        steam_group_layout.addLayout(steam_folder_layout)
        steam_group_layout.addLayout(game_id_layout)
        
        # Create group
        steam_group = QGroupBox(
            self.translations.get("indirect_file_sel_label", "Steam Integration")
        )
        steam_group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        steam_group.setLayout(steam_group_layout)
        
        return steam_group
    
    def create_separator_widget(self, text: str = "OR") -> QWidget:
        """Create a separator widget with text"""
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Plain)
        line1.setStyleSheet("color: white; background-color: white;")
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Plain)
        line2.setStyleSheet("color: white; background-color: white;")
        
        label = QLabel(self.translations.get("OR", text))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white; font-weight: bold;")
        
        layout = QHBoxLayout()
        layout.addWidget(line1)
        layout.addWidget(label)
        layout.addWidget(line2)
        
        box = QGroupBox("")
        box.setFlat(False)
        box.setLayout(layout)
        
        return box
    
    def create_info_bar(self) -> QWidget:
        """Create information bar with game name and version"""
        lang_layout = QHBoxLayout()
        
        # Game name label
        self.parent.gamename_label = QLabel(
            f"{self.translations.get('gamename', 'Game:')} {self.translations.get('unknown', 'Unknown')}"
        )
        lang_layout.addWidget(self.parent.gamename_label)
        
        # Vertical separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        lang_layout.addWidget(line)
        
        # File version label
        self.parent.version_label = QLabel(
            f"{self.translations.get('file_version', 'Version:')} {self.translations.get('unknown', 'Unknown')}"
        )
        lang_layout.addWidget(self.parent.version_label)
        
        # Create container
        box = QGroupBox("")
        box.setFlat(False)
        box.setLayout(lang_layout)
        
        return box
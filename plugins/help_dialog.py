from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QTextBrowser, QPushButton, QSplitter, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt

class HelpDialog(QDialog):
    def __init__(self, parent=None, translations=None):
        super().__init__(parent)
        self.parent_window = parent  # Store reference to parent window
        self.translations = translations or {}
        self.setWindowTitle(self.translations.get("help_title", "Help"))
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel(self.translations.get("search", "Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translations.get("help_search_placeholder", "Search topics..."))
        self.search_input.textChanged.connect(self.filter_tree)
        
        # Setup custom context menu for the search input
        if parent and hasattr(parent, 'context_menu_manager'):
            parent.context_menu_manager.setup_lineedit(self.search_input)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Splitter for Tree and Description
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Tree of topics
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(self.translations.get("help_topics", "Topics"))
        self.tree.currentItemChanged.connect(self.on_item_changed)
        splitter.addWidget(self.tree)
        
        # Right side: Description
        self.description = QTextBrowser()
        self.description.setOpenExternalLinks(True)
        splitter.addWidget(self.description)
        
        # Set initial sizes (30% tree, 70% description)
        splitter.setSizes([240, 560])
        
        layout.addWidget(splitter)
        
        # Close button
        close_btn = QPushButton(self.translations.get("close", "Close"))
        close_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.populate_tree()
        
        # Select the first item (Welcome/General) on dialog open
        first_item = self.tree.topLevelItem(0)
        if first_item:
            self.tree.setCurrentItem(first_item)
        
    def populate_tree(self):
        """Populate the help topics tree"""
        # Define help structure
        # Key is the translation key for the title
        # Value is either a dict (submenu) or a string (translation key for description)
        # For submenus, we now expect a tuple: (description_key, submenu_dict)
        
        structure = {
            "help_general": "help_general_desc",
            "help_file_menu": ("help_file_menu_desc", {
                "help_file_open": "help_file_open_desc",
                "help_file_save": "help_file_save_desc",
                "help_file_export": "help_file_export_desc",
            }),
            "help_edit_menu": ("help_edit_menu_desc", {
                "help_edit_search": "help_edit_search_desc",
                "help_edit_replace": "help_edit_replace_desc",
            }),
            "help_steam_integration": "help_steam_integration_desc",
            "help_tooltips": ("help_tooltips_desc", {
                "main_window_group": ("help_general_desc", {
                    "man_select_file_label": "tooltip_man_select_file",
                    "steam_folder_label": "tooltip_steam_folder",
                    "game_id_label": "tooltip_game_id",
                    "get_ach": "tooltip_get_ach_manual",
                    "auto": "tooltip_steam_auto",
                    "select_steam_folder": "tooltip_select_steam_folder",
                    "clear_and_paste": "tooltip_clear_paste",
                    "use_steam_name": "tooltip_use_steam_name",
                    "translation_lang": "tooltip_translation_lang",
                    "search": "tooltip_search",
                    "tooltip_table": "tooltip_table",
                    "show_user_game_stats": "tooltip_show_user_game_stats",
                }),
                "file": ("tooltip_menu_file", {
                    "export_import": ("tooltip_menu_export", {
                        "export_all": "tooltip_export_all",
                        "export_for_translate": "tooltip_export_for_translate",
                        "import_csv": "tooltip_import_csv",
                        "export_bin": "tooltip_export_bin",
                    }),
                    "save": ("tooltip_menu_save", {
                        "save_bin_known": "tooltip_save_bin_known",
                        "save_bin_unknown": "tooltip_save_bin_unknown",
                    }),
                    "delete_stats_file": "tooltip_delete_stats_file",
                    "exit": "tooltip_exit",
                }),
                "edit": ("tooltip_menu_edit", {
                    "copy": "tooltip_copy",
                    "paste": "tooltip_paste",
                    "cut": "tooltip_cut",
                    "delete": "tooltip_delete",
                    "redo": "tooltip_redo",
                    "undo": "tooltip_undo",
                    "replace_in_column": "tooltip_replace_in_column",
                    "columns": "tooltip_menu_columns",
                }),
                "language": ("tooltip_menu_language", {
                    "lang_sel": "tooltip_switch_lang",
                }),
                "appearance": ("tooltip_menu_appearance", {
                    "theme": "tooltip_menu_theme",
                    "accent_color": "tooltip_menu_accent",
                    "font_weight": "tooltip_menu_font_weight",
                    "font_size": "tooltip_menu_font_size",
                }),
                "help": ("tooltip_menu_help", {
                    "help_title": "tooltip_help_dialog",
                    "about": "tooltip_menu_about",
                }),
            }),
        }
        
        self._add_items(self.tree.invisibleRootItem(), structure)
        
        # Expand all by default
        self.tree.expandAll()
        
    def _add_items(self, parent_item, items):
        for key, value in items.items():
            title = self.translations.get(key, key)
            item = QTreeWidgetItem(parent_item, [title])
            
            if isinstance(value, tuple) and len(value) == 2:
                # It's a category with description
                desc_key, submenu = value
                item.setData(0, Qt.ItemDataRole.UserRole, desc_key)
                self._add_items(item, submenu)
            elif isinstance(value, dict):
                # It's a category without description (legacy support, though we plan to have descriptions)
                item.setData(0, Qt.ItemDataRole.UserRole, "") 
                self._add_items(item, value)
            else:
                # It's a leaf node with description
                desc_key = value
                item.setData(0, Qt.ItemDataRole.UserRole, desc_key)

    def filter_tree(self, text):
        """Filter tree items based on search text"""
        search_text = text.lower()
        
        def strip_html(html_text):
            """Strip HTML tags from text for searching"""
            if not html_text:
                return ""
            # Simple HTML tag removal
            import re
            # Remove HTML tags
            clean_text = re.sub(r'<[^>]+>', '', html_text)
            # Decode common HTML entities
            clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            return clean_text
        
        def search_item(item):
            # Check if item matches
            item_text = item.text(0).lower()
            
            # Get description text and strip HTML tags for searching
            desc_key = item.data(0, Qt.ItemDataRole.UserRole)
            if desc_key:
                desc_html = self.translations.get(desc_key, "")
                desc_text = strip_html(desc_html).lower()
            else:
                desc_text = ""
            
            # Search in both title and description content
            match = search_text in item_text or search_text in desc_text
            
            # Check children
            child_match = False
            for i in range(item.childCount()):
                if search_item(item.child(i)):
                    child_match = True
            
            # Show if match or child match
            should_show = match or child_match or not search_text
            item.setHidden(not should_show)
            
            # Expand if child match or if this item matches
            if child_match or (match and search_text):
                item.setExpanded(True)
                
            return should_show

        # Iterate over top-level items
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            search_item(root.child(i))
                
    def on_item_changed(self, current, previous):
        if not current:
            return
            
        desc_key = current.data(0, Qt.ItemDataRole.UserRole)
        if desc_key:
            description = self.translations.get(desc_key, "No description available.")
            self.description.setHtml(description)
        else:
            self.description.clear()

"""
Custom Context Menu Plugin
Provides unified context menu with icons for QLineEdit and QTableWidget widgets.
"""

from functools import partial
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMenu, QStyle, QApplication, QLineEdit, QTableWidget


class ContextMenuManager:
    """Manager for custom context menus with icons and translations"""
    
    def __init__(self, parent, translations=None):
        """
        Initialize context menu manager.
        
        Args:
            parent: Parent widget (usually main window)
            translations: Dictionary with translations
        """
        self.parent = parent
        self.translations = translations or {}
    
    def update_translations(self, translations):
        """Update translations dictionary"""
        self.translations = translations
    
    def _get_style(self):
        """Get current style from parent"""
        return self.parent.style()
    
    def setup_lineedit(self, line_edit: QLineEdit):
        """
        Setup custom context menu for a QLineEdit widget.
        
        Args:
            line_edit: QLineEdit widget to setup
        """
        # Disconnect any existing connections first
        try:
            line_edit.customContextMenuRequested.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        
        line_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        line_edit.customContextMenuRequested.connect(
            partial(self._show_lineedit_menu, line_edit)
        )
    
    def setup_table(self, table: QTableWidget, extra_actions=None):
        """
        Setup custom context menu for a QTableWidget widget.
        
        Args:
            table: QTableWidget widget to setup
            extra_actions: List of additional QAction objects to add at the end
        """
        self._table = table
        self._table_extra_actions = extra_actions or []
        
        # Disconnect any existing connections first
        try:
            table.customContextMenuRequested.disconnect()
        except TypeError:
            pass
        
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_table_menu)
    
    def _get_icon(self, theme_name: str, fallback_pixmap):
        """Get icon from theme with fallback to standard pixmap"""
        return QIcon.fromTheme(theme_name, self._get_style().standardIcon(fallback_pixmap))
    
    def _show_lineedit_menu(self, line_edit: QLineEdit, pos):
        """Show context menu for QLineEdit"""
        menu = QMenu(self.parent)
        
        # Undo
        undo_action = menu.addAction(
            self._get_icon("edit-undo", QStyle.StandardPixmap.SP_ArrowBack),
            self.translations.get("undo", "Undo")
        )
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(line_edit.undo)
        undo_action.setEnabled(line_edit.isUndoAvailable())
        
        # Redo
        redo_action = menu.addAction(
            self._get_icon("edit-redo", QStyle.StandardPixmap.SP_ArrowForward),
            self.translations.get("redo", "Redo")
        )
        redo_action.setShortcut("Ctrl+Shift+Z")
        redo_action.triggered.connect(line_edit.redo)
        redo_action.setEnabled(line_edit.isRedoAvailable())
        
        menu.addSeparator()
        
        # Cut
        cut_action = menu.addAction(
            self._get_icon("edit-cut", QStyle.StandardPixmap.SP_DialogDiscardButton),
            self.translations.get("cut", "Cut")
        )
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(line_edit.cut)
        cut_action.setEnabled(line_edit.hasSelectedText())
        
        # Copy
        copy_action = menu.addAction(
            self._get_icon("edit-copy", QStyle.StandardPixmap.SP_FileDialogNewFolder),
            self.translations.get("copy", "Copy")
        )
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(line_edit.copy)
        copy_action.setEnabled(line_edit.hasSelectedText())
        
        # Paste
        paste_action = menu.addAction(
            self._get_icon("edit-paste", QStyle.StandardPixmap.SP_DialogApplyButton),
            self.translations.get("paste", "Paste")
        )
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(line_edit.paste)
        paste_action.setEnabled(bool(QApplication.clipboard().text()))
        
        # Delete
        delete_action = menu.addAction(
            self._get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon),
            self.translations.get("delete", "Delete")
        )
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(lambda: line_edit.del_() if line_edit.hasSelectedText() else None)
        delete_action.setEnabled(line_edit.hasSelectedText())
        
        menu.addSeparator()
        
        # Select All
        select_all_action = menu.addAction(
            self._get_icon("edit-select-all", QStyle.StandardPixmap.SP_DialogYesButton),
            self.translations.get("select_all", "Select All")
        )
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(line_edit.selectAll)
        select_all_action.setEnabled(bool(line_edit.text()))
        
        menu.exec(line_edit.mapToGlobal(pos))
    
    def _show_table_menu(self, pos):
        """Show context menu for QTableWidget"""
        menu = QMenu(self.parent)
        
        # Undo
        undo_action = menu.addAction(
            self._get_icon("edit-undo", QStyle.StandardPixmap.SP_ArrowBack),
            self.translations.get("undo", "Undo")
        )
        undo_action.setShortcut("Ctrl+Z")
        if hasattr(self.parent, 'undo'):
            undo_action.triggered.connect(self.parent.undo)
            undo_action.setEnabled(bool(getattr(self.parent, 'undo_stack', [])))
        
        # Redo
        redo_action = menu.addAction(
            self._get_icon("edit-redo", QStyle.StandardPixmap.SP_ArrowForward),
            self.translations.get("redo", "Redo")
        )
        redo_action.setShortcut("Ctrl+Shift+Z")
        if hasattr(self.parent, 'redo'):
            redo_action.triggered.connect(self.parent.redo)
            redo_action.setEnabled(bool(getattr(self.parent, 'redo_stack', [])))
        
        menu.addSeparator()
        
        # Cut
        cut_action = menu.addAction(
            self._get_icon("edit-cut", QStyle.StandardPixmap.SP_DialogDiscardButton),
            self.translations.get("cut", "Cut")
        )
        cut_action.setShortcut("Ctrl+X")
        if hasattr(self.parent, 'cut_selection_to_clipboard'):
            cut_action.triggered.connect(self.parent.cut_selection_to_clipboard)
        
        # Copy
        copy_action = menu.addAction(
            self._get_icon("edit-copy", QStyle.StandardPixmap.SP_FileDialogNewFolder),
            self.translations.get("copy", "Copy")
        )
        copy_action.setShortcut("Ctrl+C")
        if hasattr(self.parent, 'copy_selection_to_clipboard'):
            copy_action.triggered.connect(self.parent.copy_selection_to_clipboard)
        
        # Paste
        paste_action = menu.addAction(
            self._get_icon("edit-paste", QStyle.StandardPixmap.SP_DialogApplyButton),
            self.translations.get("paste", "Paste")
        )
        paste_action.setShortcut("Ctrl+V")
        if hasattr(self.parent, 'paste_from_clipboard'):
            paste_action.triggered.connect(self.parent.paste_from_clipboard)
        
        # Delete
        delete_action = menu.addAction(
            self._get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon),
            self.translations.get("delete", "Delete")
        )
        delete_action.setShortcut("Delete")
        if hasattr(self.parent, 'clear_selection'):
            delete_action.triggered.connect(self.parent.clear_selection)
        
        menu.addSeparator()
        
        # Select All
        select_all_action = menu.addAction(
            self._get_icon("edit-select-all", QStyle.StandardPixmap.SP_DialogYesButton),
            self.translations.get("select_all", "Select All")
        )
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self._table.selectAll)
        
        # Add extra actions with separator
        if self._table_extra_actions:
            menu.addSeparator()
            for action in self._table_extra_actions:
                menu.addAction(action)
        
        menu.exec(self._table.viewport().mapToGlobal(pos))
    
    def create_table_actions(self):
        """
        Create QAction objects for table operations that can be used in menus and shortcuts.
        Returns a dictionary of actions.
        """
        actions = {}
        
        actions['undo'] = QAction(
            self._get_icon("edit-undo", QStyle.StandardPixmap.SP_ArrowBack),
            self.translations.get("undo", "Undo"),
            self.parent
        )
        actions['undo'].setShortcut("Ctrl+Z")
        if hasattr(self.parent, 'undo'):
            actions['undo'].triggered.connect(self.parent.undo)
        
        actions['redo'] = QAction(
            self._get_icon("edit-redo", QStyle.StandardPixmap.SP_ArrowForward),
            self.translations.get("redo", "Redo"),
            self.parent
        )
        actions['redo'].setShortcut("Ctrl+Shift+Z")
        if hasattr(self.parent, 'redo'):
            actions['redo'].triggered.connect(self.parent.redo)
        
        actions['cut'] = QAction(
            self._get_icon("edit-cut", QStyle.StandardPixmap.SP_DialogDiscardButton),
            self.translations.get("cut", "Cut"),
            self.parent
        )
        actions['cut'].setShortcut("Ctrl+X")
        if hasattr(self.parent, 'cut_selection_to_clipboard'):
            actions['cut'].triggered.connect(self.parent.cut_selection_to_clipboard)
        
        actions['copy'] = QAction(
            self._get_icon("edit-copy", QStyle.StandardPixmap.SP_FileDialogNewFolder),
            self.translations.get("copy", "Copy"),
            self.parent
        )
        actions['copy'].setShortcut("Ctrl+C")
        if hasattr(self.parent, 'copy_selection_to_clipboard'):
            actions['copy'].triggered.connect(self.parent.copy_selection_to_clipboard)
        
        actions['paste'] = QAction(
            self._get_icon("edit-paste", QStyle.StandardPixmap.SP_DialogApplyButton),
            self.translations.get("paste", "Paste"),
            self.parent
        )
        actions['paste'].setShortcut("Ctrl+V")
        if hasattr(self.parent, 'paste_from_clipboard'):
            actions['paste'].triggered.connect(self.parent.paste_from_clipboard)
        
        actions['delete'] = QAction(
            self._get_icon("edit-delete", QStyle.StandardPixmap.SP_TrashIcon),
            self.translations.get("delete", "Delete"),
            self.parent
        )
        actions['delete'].setShortcut("Delete")
        if hasattr(self.parent, 'clear_selection'):
            actions['delete'].triggered.connect(self.parent.clear_selection)
        
        actions['select_all'] = QAction(
            self._get_icon("edit-select-all", QStyle.StandardPixmap.SP_DialogYesButton),
            self.translations.get("select_all", "Select All"),
            self.parent
        )
        actions['select_all'].setShortcut("Ctrl+A")
        
        actions['find_replace'] = QAction(
            self._get_icon("edit-find-replace", QStyle.StandardPixmap.SP_FileDialogInfoView),
            self.translations.get("search_replace", "Search and Replace"),
            self.parent
        )
        actions['find_replace'].setShortcut("Ctrl+F")
        if hasattr(self.parent, 'show_find_replace_dialog'):
            actions['find_replace'].triggered.connect(self.parent.show_find_replace_dialog)
        
        return actions

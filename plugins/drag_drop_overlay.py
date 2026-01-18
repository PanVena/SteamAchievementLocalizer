import os
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import Qt, QEvent, QTimer, QObject
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor

from .steam_lang_codes import get_display_name

class DragDropOverlay(QWidget):
    def __init__(self, parent, on_file_dropped):
        super().__init__(parent)
        self.on_file_dropped = on_file_dropped
        self.message = ""
        
        # Ensure it stays on top and covers the parent
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAcceptDrops(True)
        
        # NOTE: Removed Qt.Tool to keep it attached to the main window client area
        # We just want it to be a child widget that overlays everything
        self.hide()
        
        # Timer to check if drag has left the window
        self.position_check_timer = QTimer(self)
        self.position_check_timer.timeout.connect(self._check_drag_position)
        self.position_check_timer.setInterval(10)  # Check every 100ms

    def show_overlay(self, message=""):
        self.message = message
        self.resize(self.parent().size())
        self.raise_()
        self.show()
        self.update() # Ensure repaint with new message
        # Start checking position when overlay is shown
        self.position_check_timer.start()

    def hide_overlay(self):
        self.position_check_timer.stop()
        self.hide()
    
    def _check_drag_position(self):
        """Check if mouse cursor is still over parent window"""
        if self.isVisible():
            global_pos = QCursor.pos()
            parent_widget = self.parent()
            local_pos = parent_widget.mapFromGlobal(global_pos)
            
            # Also check if parent window has focus - hide if it lost focus
            if not parent_widget.isActiveWindow():
                self.hide_overlay()
                return
            
            if not parent_widget.rect().contains(local_pos):
                # Mouse is outside parent window - hide overlay
                self.hide_overlay()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
        
        # Dashed border
        pen = QPen(QColor(255, 255, 255, 200), 4, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        margin = 40
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.drawRoundedRect(rect, 20, 20)
        
        # Text
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 240))
        
        # Get translation from parent window
        translations = getattr(self.parent(), 'translations', {})
        
        if self.message:
            text = self.message
        else:
            text = translations.get("drag_drop_hint", "Drop .bin file here")
            
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check file extension if possible
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path.lower().endswith(('.bin', '.csv')):
                     event.acceptProposedAction()
                     return
        event.ignore()

    def dragMoveEvent(self, event):
        """Accept drag move events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.hide_overlay()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if os.path.isfile(file_path):
                    self.on_file_dropped(file_path)
        self.hide_overlay()
        event.acceptProposedAction()
    
    # We might need to catch mouse events to discard them if they happen on overlay
    def mousePressEvent(self, event):
        self.hide_overlay()

class DragDropPlugin(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.overlay = DragDropOverlay(main_window, self.open_file)
        
        # Install event filter to catch resize and initial drag enter on main window
        self.main_window.installEventFilter(self)
        self.main_window.setAcceptDrops(True)
        
    def eventFilter(self, obj, event):
        if obj is self.main_window:
            if event.type() == QEvent.Type.Resize:
                if not self.overlay.isHidden():
                    self.overlay.resize(self.main_window.size())
            elif event.type() == QEvent.Type.DragEnter:
                # Main window received drag enter -> show overlay
                if event.mimeData().hasUrls():
                    # Validate file extensions BEFORE showing overlay
                    # If we show overlay for invalid files, it will reject the drag and 
                    # might not receive the dragLeaveEvent properly, causing it to get stuck.
                    urls = event.mimeData().urls()
                    if urls:
                        path = urls[0].toLocalFile()
                        lower_path = path.lower()
                        
                        translations = getattr(self.main_window, 'translations', {})
                        message = ""
                        
                        if lower_path.endswith('.bin'):
                             message = translations.get("drag_drop_hint", "Drop .bin file here")
                             self.main_window.activateWindow()
                             self.main_window.raise_()
                             self.overlay.show_overlay(message)
                             event.acceptProposedAction()
                             return True
                        elif lower_path.endswith('.csv'):
                             # Import CSV logic
                             translations = getattr(self.main_window, 'translations', {})
                             target_lang_code = "english" # Default
                             
                             if hasattr(self.main_window, 'get_target_language'):
                                 target_lang_code = self.main_window.get_target_language()
                             
                             target_lang_name = get_display_name(target_lang_code)
                             
                             # Check if we need to auto-load game (data_rows empty)
                             is_empty = not hasattr(self.main_window, 'data_rows') or not self.main_window.data_rows
                             
                             game_id_found = None
                             if is_empty and hasattr(self.main_window, 'csv_handler'):
                                 # Peek at CSV to find game_id
                                 try:
                                     preview = self.main_window.csv_handler.get_column_preview(path, max_rows=1)
                                     if preview['valid'] and preview['header']:
                                         potential_id = preview['header'][-1].strip()
                                         if potential_id.isdigit():
                                             game_id_found = potential_id
                                 except Exception:
                                     pass

                             if game_id_found:
                                 gamename = "Unknown"
                                 if hasattr(self.main_window, 'get_game_name_for_id'):
                                     gamename = self.main_window.get_game_name_for_id(game_id_found)
                                 
                                 # "Open game {gamename} ({game_id}) and import to: " + Lang
                                 msg_template = translations.get("drag_drop_open_game_hint", "Open game {gamename} ({game_id}) and import to: ")
                                 message = msg_template.format(gamename=gamename, game_id=game_id_found) + target_lang_name
                             elif hasattr(self.main_window, 'get_target_language'):
                                 message = translations.get("drag_drop_csv_hint", "Drop lines to: ") + target_lang_name
                             else:
                                 message = "Drop CSV to import"
                                 
                             self.main_window.activateWindow()
                             self.main_window.raise_()
                             self.overlay.show_overlay(message)
                             event.acceptProposedAction()
                             return True
                                 
            elif event.type() == QEvent.Type.DragLeave:
                # Don't hide on DragLeave - it fires too often when moving between child widgets
                # Overlay will hide on drop or when user clicks it
                pass
        return False

    def open_file(self, file_path):
        # Integration logic
        # Note: We don't check for unsaved changes here because select_stats_bin_path() 
        # already performs this check. Doing it here would cause a duplicate prompt.
        
        # Check file extension
        if file_path.lower().endswith('.csv'):
             if hasattr(self.main_window, 'import_dropped_csv'):
                 self.main_window.import_dropped_csv(file_path)
             return
        
        # Default behavior for .bin files
        # Fill the path in the line edit
        if hasattr(self.main_window, 'stats_bin_path_path'):
             self.main_window.stats_bin_path_path.setText(file_path)
             
             # Trigger the load button logic
             if hasattr(self.main_window, 'select_stats_bin_path'):
                 # select_stats_bin_path() will check for unsaved changes and load the file
                 self.main_window.select_stats_bin_path()
             else:
                 translations = getattr(self.main_window, 'translations', {})
                 info_title = translations.get("info", "Info")
                 msg_template = translations.get("file_dropped_msg", "File dropped: {path}")
                 QMessageBox.warning(self.main_window, info_title, msg_template.format(path=file_path))

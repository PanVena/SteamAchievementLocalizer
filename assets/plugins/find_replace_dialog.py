from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFrame, QWidget

from PyQt6.QtGui import QColor, QBrush, QTextCharFormat
from PyQt6.QtCore import Qt
from .steam_lang_codes import get_display_name

import re

class FindReplaceDialog(QDialog):
    def __init__(self, parent, headers):
        super().__init__(parent)
        self.setWindowTitle(parent.translations.get("search_replace"))
        self.translations = getattr(self.parent(), "translations", {})
        self.setMinimumWidth(500)

        self.table = parent.table
        self.data_rows = parent.data_rows
        self.headers = headers
        self.matches = []

        self.status = True

        self.layout = QVBoxLayout()


        btns_choice_layout = QHBoxLayout()
        self.just_search_btn = QPushButton(self.translations.get("search"))
        self.replacing_btn = QPushButton(self.translations.get("search_replace"))

        self.just_search_btn.clicked.connect(lambda: self.change_mode(True))
        self.replacing_btn.clicked.connect(lambda: self.change_mode(False))

        btns_choice_layout.addWidget(self.just_search_btn)
        btns_choice_layout.addWidget(self.replacing_btn)
        self.layout.addLayout(btns_choice_layout)


        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)


        self.content_layout = QVBoxLayout()
        self.layout.addLayout(self.content_layout)

        self.setLayout(self.layout)
        self.set_window() 

    def change_mode(self, mode: bool):
        if self.status != mode:
            self.status = mode
            self.set_window()
            

    def set_window(self):

        current_text = ""
        if hasattr(self, "find_edit") and self.find_edit is not None:
            current_text = self.find_edit.text()


        if hasattr(self, "content_widget"):
            self.layout.removeWidget(self.content_widget)
            self.content_widget.deleteLater()

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.layout.addWidget(self.content_widget)

        
        if self.status:  
            form_layout = QHBoxLayout()
            self.find_edit = QLineEdit()
            self.find_edit.setPlaceholderText(self.translations.get("seeeking_for_what"))
            self.find_edit.setText(current_text)
            form_layout.addWidget(QLabel(self.translations.get("search_text")))
            form_layout.addWidget(self.find_edit)
            self.content_layout.addLayout(form_layout)

            btn_layout = QHBoxLayout()
            self.close_btn = QPushButton(self.translations.get("close"))
            btn_layout.addWidget(self.close_btn)
            self.content_layout.addLayout(btn_layout)

            self.find_edit.textChanged.connect(lambda text: self.parent().global_search_in_table(text))
            self.close_btn.clicked.connect(self.accept)
            self.adjustSize()

        else:  
            form_layout = QHBoxLayout()
            self.find_edit = QLineEdit()
            self.find_edit.setPlaceholderText(self.translations.get("seeeking_for_what"))
            self.find_edit.setText(current_text)
            self.replace_edit = QLineEdit()
            self.replace_edit.setPlaceholderText(self.translations.get("by_what"))
            form_layout.addWidget(QLabel(self.translations.get("search_text")))
            form_layout.addWidget(self.find_edit)
            form_layout.addWidget(QLabel(self.translations.get("replace_text")))
            form_layout.addWidget(self.replace_edit)
            self.content_layout.addLayout(form_layout)

            col_layout = QHBoxLayout()
            self.column_combo = QComboBox()
            non_key_headers = [h for h in self.headers if h != 'key']
            for header in non_key_headers:
                display_name = get_display_name(header)
                self.column_combo.addItem(display_name, header)
            col_layout.addWidget(QLabel(self.translations.get("column")))
            col_layout.addWidget(self.column_combo)
            self.content_layout.addLayout(col_layout)

            self.match_label = QLabel(self.translations.get("found_nothing"))
            self.content_layout.addWidget(self.match_label)

            btn_layout = QHBoxLayout()
            self.replace_btn = QPushButton(self.translations.get("replace_all"))
            self.close_btn = QPushButton(self.translations.get("close"))
            btn_layout.addWidget(self.replace_btn)
            btn_layout.addWidget(self.close_btn)
            self.content_layout.addLayout(btn_layout)

            self.close_btn.clicked.connect(self.accept)

            self.find_edit.textChanged.connect(self.update_matches)
            self.column_combo.currentIndexChanged.connect(self.update_matches)
            self.replace_btn.clicked.connect(self.replace_all)
            self.close_btn.clicked.connect(self.accept)
            self.replace_edit.textChanged.connect(self.update_matches)

            self.update_matches()
            self.adjustSize()



    def update_matches(self):
        translations = getattr(self.parent(), "translations", {})
        find_text = self.find_edit.text()
        # Get the actual column header from combo box data
        col = self.column_combo.currentData() or self.column_combo.currentText()
        self.matches = []

        col_idx = self.parent().headers.index(col) if col in self.parent().headers else -1
        match_count = 0

        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)


        if col_idx != -1:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col_idx)
                if item:
                    plain_text = self.parent().data_rows[row].get(col, "")
                    item.setText(plain_text)

        if not find_text or not col or col_idx == -1:
            self.match_label.setText(translations.get("found_nothing"))
            # CLEAR DELEGATE HIGHLIGHT
            self.parent().highlight_delegate.set_highlight("")
            self.parent().highlight_delegate.highlight_column = -1
            self.parent().table.viewport().update()
            return

        for row in range(self.table.rowCount()):
            item = self.table.item(row, col_idx)
            if item:
                val = item.text()
                occurrences = len(re.findall(re.escape(find_text), val, flags=re.IGNORECASE))
                if occurrences > 0:
                    match_count += occurrences
                    self.matches.append((row, col_idx))
                else:
                    self.table.setRowHidden(row, True)

        msg = translations.get("found").format(match_count=match_count)
        self.match_label.setText(msg)
        # DELEGATE HIGHLIGHT
        self.parent().highlight_delegate.set_highlight(find_text)
        self.parent().highlight_delegate.highlight_column = col_idx
        self.parent().table.viewport().update()



    def highlight_occurrences(self, text, find_text):
        if not find_text:
            return text

        pattern = re.compile(re.escape(find_text), re.IGNORECASE)
        # HTML escape
        def html_escape(s):
            return (
                s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;")
            )
        text = html_escape(text)
        return pattern.sub(lambda m: f"<span style='background: orange;'>{html_escape(m.group(0))}</span>", text)

    def replace_all(self):
        # Get the actual column header from combo box data
        col = self.column_combo.currentData() or self.column_combo.currentText()
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        col_idx = self.parent().headers.index(col)
        changed = 0

        for row in range(self.table.rowCount()):
            item = self.table.item(row, col_idx)
            if item:
                old_plain = self.parent().data_rows[row].get(col, "")
                if find_text and find_text.lower() in old_plain.lower():
                    new_val = re.sub(
                        re.escape(find_text), replace_text, old_plain, flags=re.IGNORECASE
                    )
                    item.setText(new_val)
                    self.parent().data_rows[row][col] = new_val
                    changed += 1
                else:
                    item.setText(old_plain)
        self.update_matches()

    def cleaner(self):
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

        self.parent().highlight_delegate.set_highlight("")
        self.parent().highlight_delegate.highlight_column = -1
        self.parent().table.viewport().update()

    def accept(self):
        self.cleaner()
        super().accept()
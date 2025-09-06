from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton

from PyQt6.QtGui import QColor, QBrush, QTextCharFormat
from PyQt6.QtCore import Qt

import re

class FindReplaceDialog(QDialog):
    def __init__(self, parent, headers):
        super().__init__(parent)
        self.setWindowTitle(parent.translations.get("search_replace"))
        self.setMinimumWidth(400)
        self.table = parent.table
        self.data_rows = parent.data_rows
        self.headers = headers
        self.matches = []

        layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText(parent.translations.get("seeeking_for_what"))
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText(parent.translations.get("by_what"))
        form_layout.addWidget(QLabel(parent.translations.get("search_text")))
        form_layout.addWidget(self.find_edit)
        form_layout.addWidget(QLabel(parent.translations.get("replace_text")))
        form_layout.addWidget(self.replace_edit)
        layout.addLayout(form_layout)

        col_layout = QHBoxLayout()
        self.column_combo = QComboBox()
        self.column_combo.addItems([h for h in headers if h != 'key'])
        col_layout.addWidget(QLabel(parent.translations.get("column")))
        col_layout.addWidget(self.column_combo)
        layout.addLayout(col_layout)

        self.match_label = QLabel(parent.translations.get("found_nothing"))
        layout.addWidget(self.match_label)

        btn_layout = QHBoxLayout()
        self.replace_btn = QPushButton(parent.translations.get("replace_all"))
        self.close_btn = QPushButton(parent.translations.get("close"))
        btn_layout.addWidget(self.replace_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.find_edit.textChanged.connect(self.update_matches)
        self.column_combo.currentIndexChanged.connect(self.update_matches)
        self.replace_btn.clicked.connect(self.replace_all)
        self.close_btn.clicked.connect(self.accept)
        self.replace_edit.textChanged.connect(self.update_matches)

        self.update_matches()

    def update_matches(self):
        translations = getattr(self.parent(), "translations", {})
        find_text = self.find_edit.text()
        col = self.column_combo.currentText()
        self.matches = []

        col_idx = self.table.parent().headers.index(col) if col in self.table.parent().headers else -1
        match_count = 0

       
        if col_idx != -1:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col_idx)
                if item:
                    plain_text = self.data_rows[row].get(col, "")
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
                    pass
        
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
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        col = self.column_combo.currentText()
        col_idx = self.table.parent().headers.index(col)
        changed = 0

        for row in range(self.table.rowCount()):
            item = self.table.item(row, col_idx)
            if item:
                old_plain = self.data_rows[row].get(col, "")
                if find_text and find_text.lower() in old_plain.lower():
                    new_val = re.sub(
                        re.escape(find_text), replace_text, old_plain, flags=re.IGNORECASE
                    )
                    item.setText(new_val)
                    self.table.parent().data_rows[row][col] = new_val
                    changed += 1
                else:
                    item.setText(old_plain)
        self.update_matches()

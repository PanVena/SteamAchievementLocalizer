from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from .steam_lang_codes import get_display_name

class ContextLangDialog(QDialog):
    def __init__(self, headers, info_text="", mode='export', parent=None):
        super().__init__(parent)
        translations = getattr(self.parent(), "translations", {})
        self.setWindowTitle(translations.get("lang_sel_dia"))
        self.setMinimumSize(300, 200)
        layout = QVBoxLayout(self)

        if info_text:
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        self.combo = QComboBox()
        header_items = [h for h in headers if h != "key" and h != "icon"]
        
        # Store mapping between display names and original headers
        self.header_mapping = {}
        
        if mode == 'export':
            layout.addWidget(QLabel(translations.get("choose_export")))
        else:
            layout.addWidget(QLabel(translations.get("choose_import")))
        
        # Add items with display names but keep original headers as data
        for header in header_items:
            display_name = get_display_name(header)
            self.combo.addItem(display_name, header)  # Store original header as data
            self.header_mapping[display_name] = header
            
        layout.addWidget(self.combo)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

        self.setLayout(layout)

    def get_selected(self):
        # Return the original header name, not the display name
        current_data = self.combo.currentData()
        return {
            "context_col": current_data if current_data else self.combo.currentText()
        }
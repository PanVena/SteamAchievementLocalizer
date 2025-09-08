from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton

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
        header_items = [h for h in headers if h != "key"]
        if mode == 'export':
            layout.addWidget(QLabel(translations.get("choose_export")))
        else:
            layout.addWidget(QLabel(translations.get("choose_import")))
        self.combo.addItems(header_items)
        layout.addWidget(self.combo)

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

        self.setLayout(layout)

    def get_selected(self):
        return {
            "context_col": self.combo.currentText()
        }
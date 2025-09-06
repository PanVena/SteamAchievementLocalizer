from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtGui import QTextDocument, QPalette, QColor
import re

class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_text = ""
        self.highlight_color = QColor("orange")
        self.highlight_column = -1  

    def set_highlight(self, text, color=None):
        self.highlight_text = text
        if color is not None:
            self.highlight_color = QColor(color)

    def paint(self, painter, option, index):
        
        if self.highlight_column != -1 and index.column() != self.highlight_column:
            super().paint(painter, option, index)
            return

        text = index.data()
        if not self.highlight_text or not text:
            super().paint(painter, option, index)
            return

        pattern = re.compile(re.escape(self.highlight_text), re.IGNORECASE)
        def html_escape(s):
            return (s.replace("&", "&amp;")
                      .replace("<", "&lt;")
                      .replace(">", "&gt;")
                      .replace('"', "&quot;")
                      .replace("'", "&#39;"))
        text_escaped = html_escape(str(text))
        highlighted = pattern.sub(
            lambda m: f"<span style='background-color: {self.highlight_color.name()};'>{html_escape(m.group(0))}</span>",
            text_escaped
        )

        
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.color(QPalette.ColorRole.Highlight))

        doc = QTextDocument()
        doc.setHtml(highlighted)
        painter.save()
        painter.translate(option.rect.left(), option.rect.top())
        doc.setTextWidth(option.rect.width())
        doc.drawContents(painter)
        painter.restore()

    def sizeHint(self, option, index):
        text = index.data()
        doc = QTextDocument()
        doc.setHtml(str(text) if text else "")
        sz = doc.size().toSize()
        print(f"SizeHint for row {index.row()}, col {index.column()} = {sz}")
        return sz
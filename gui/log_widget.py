from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor, QColor
from PyQt6.QtCore import Qt

class LogWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFontFamily("Courier New")
        self.document().setMaximumBlockCount(20)

    def append_log(self, text: str):
        self.setTextColor(QColor(200, 200, 200))
        self.append(text)
        self.moveCursor(QTextCursor.MoveOperation.End)

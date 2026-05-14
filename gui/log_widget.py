from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor, QColor
from PyQt6.QtCore import Qt

class LogWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFontFamily("Courier New")
        self.document().setMaximumBlockCount(100)

    def append_log(self, text: str):
        self.setTextColor(QColor(200, 200, 200))
        self.append(text)
        # Проверяем, что есть хотя бы один блок, чтобы избежать ошибки
        if self.document().blockCount() > 0:
            self.moveCursor(QTextCursor.MoveOperation.End)

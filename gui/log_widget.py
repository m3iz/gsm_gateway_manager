"""
Log widget displaying TX/RX messages with color coding.
"""
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor, QColor
from PyQt6.QtCore import Qt

class LogWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFontFamily("Courier New")
        self.document().setMaximumBlockCount(1000)  # Limit log size

    def append_log(self, text: str):
        """Append a log message with color based on content."""
        color = QColor(200, 200, 200)  # Default gray
        if "TX" in text:
            color = QColor(100, 200, 255)  # Light blue for TX
        elif "RX" in text:
            color = QColor(100, 255, 100)  # Light green for RX
        elif "ERROR" in text:
            color = QColor(255, 100, 100)  # Red for errors
        elif "WARN" in text:
            color = QColor(255, 255, 100)  # Yellow for warnings

        self.setTextColor(color)
        self.append(text)
        # Auto-scroll to bottom
        self.moveCursor(QTextCursor.MoveOperation.End)

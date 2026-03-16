"""
Simple logging utility for GUI log window.
"""
from typing import List, Callable

class Logger:
    def __init__(self):
        self.handlers: List[Callable[[str], None]] = []
        self.buffer = []

    def add_handler(self, handler: Callable[[str], None]):
        self.handlers.append(handler)

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        self.buffer.append(formatted)
        for handler in self.handlers:
            handler(formatted)

    def info(self, message: str):
        self.log(message, "INFO")

    def warning(self, message: str):
        self.log(message, "WARN")

    def error(self, message: str):
        self.log(message, "ERROR")

    def tx(self, command: str):
        self.log(f"TX -> {command}", "CMD")

    def rx(self, response: str):
        self.log(f"RX <- {response}", "RESP")

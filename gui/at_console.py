"""
AT command console for manual commands and logging.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLineEdit, QPushButton, QLabel)
from PyQt6.QtCore import pyqtSignal
from gsm.gsm_modem import GsmModem

class ATConsole(QWidget):
    def __init__(self, modem: GsmModem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Output area
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFontFamily("Courier New")
        layout.addWidget(QLabel("AT Command Log:"))
        layout.addWidget(self.output)

        # Input line
        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Enter AT command...")
        self.input_line.returnPressed.connect(self.send_command)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_command)

        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        # Clear button
        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.output.clear)
        layout.addWidget(self.clear_btn)

        self.setLayout(layout)

        # Connect modem URC callback
        self.modem.register_urc_callback(self.on_urc)

    def send_command(self):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            self.output.append("ERROR: Not connected")
            return

        cmd = self.input_line.text().strip()
        if not cmd:
            return

        self.logger.tx(cmd)
        self.output.append(f">>> {cmd}")

        responses = self.modem.serial.send_command(cmd)
        for line in responses:
            self.logger.rx(line)
            self.output.append(line)

        self.input_line.clear()

    def on_urc(self, line: str):
        """Handle unsolicited result codes."""
        self.output.append(f"[URC] {line}")

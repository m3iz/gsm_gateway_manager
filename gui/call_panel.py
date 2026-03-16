"""
Call automation panel with dialing controls.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QComboBox, QLineEdit, QSpinBox, QPushButton,
                             QLabel, QFormLayout)
from PyQt6.QtCore import QTimer, pyqtSignal
from gsm.gsm_modem import GsmModem

class CallPanel(QWidget):
    def __init__(self, modem: GsmModem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.calling_active = False
        self.call_timer = QTimer()
        self.call_timer.timeout.connect(self.place_call)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("Call Automation")
        form = QFormLayout()

        self.country_combo = QComboBox()
        self.country_combo.addItems(["Russia (+7)", "USA (+1)", "Ukraine (+380)", "Other"])
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 3600)
        self.delay_spin.setValue(5)
        self.delay_unit = QComboBox()
        self.delay_unit.addItems(["seconds", "minutes"])

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addWidget(self.delay_unit)

        self.start_btn = QPushButton("Start Calling")
        self.start_btn.clicked.connect(self.toggle_calling)
        self.stop_btn = QPushButton("Stop Calling")
        self.stop_btn.clicked.connect(self.stop_calling)
        self.stop_btn.setEnabled(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        form.addRow("Country:", self.country_combo)
        form.addRow("Number:", self.phone_input)
        form.addRow("Delay:", delay_layout)
        form.addRow("", btn_layout)

        group.setLayout(form)
        layout.addWidget(group)

        # Quick dial (manual)
        quick_group = QGroupBox("Manual Call")
        quick_layout = QHBoxLayout()
        self.quick_number = QLineEdit()
        self.quick_number.setPlaceholderText("Enter number")
        self.dial_btn = QPushButton("Dial")
        self.dial_btn.clicked.connect(self.manual_dial)
        self.hangup_btn = QPushButton("Hang Up")
        self.hangup_btn.clicked.connect(self.modem.hangup)
        quick_layout.addWidget(self.quick_number)
        quick_layout.addWidget(self.dial_btn)
        quick_layout.addWidget(self.hangup_btn)
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)

        layout.addStretch()
        self.setLayout(layout)

    def toggle_calling(self):
        if not self.modem.connected:
            self.logger.warning("Modem not connected")
            return
        if self.calling_active:
            self.stop_calling()
        else:
            self.start_calling()

    def start_calling(self):
        number = self.phone_input.text().strip()
        if not number:
            self.logger.warning("Please enter a phone number")
            return

        # Add country code if needed (simplified)
        self.calling_active = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.logger.info(f"Starting automated calls to {number}")

        # Calculate delay in milliseconds
        delay = self.delay_spin.value()
        if self.delay_unit.currentText() == "minutes":
            delay *= 60
        self.call_timer.start(delay * 1000)
        # Place first call immediately
        self.place_call()

    def stop_calling(self):
        self.calling_active = False
        self.call_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.logger.info("Call automation stopped")

    def place_call(self):
        if not self.modem.connected:
            self.stop_calling()
            return
        number = self.phone_input.text().strip()
        self.logger.info(f"Dialing {number}...")
        success = self.modem.dial(number)
        if success:
            self.logger.info("Call initiated")
            # In a real app, you might wait and then hang up after some time
            # For demo, hang up after 5 seconds
            QTimer.singleShot(5000, self.modem.hangup)
        else:
            self.logger.error("Call failed")

    def manual_dial(self):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            return
        number = self.quick_number.text().strip()
        if number:
            self.logger.info(f"Manual dial {number}")
            self.modem.dial(number)
            QTimer.singleShot(5000, self.modem.hangup)

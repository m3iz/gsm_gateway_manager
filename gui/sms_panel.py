"""
SMS sending panel with templates and quantity.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QRadioButton, QButtonGroup, QLineEdit,
                             QTextEdit, QSpinBox, QPushButton, QLabel,
                             QComboBox, QFormLayout)
from PyQt6.QtCore import pyqtSignal
from gsm.gsm_modem import GsmModem

class SmsPanel(QWidget):
    def __init__(self, modem: GsmModem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.templates = {
            "Welcome": "Welcome to our service!",
            "Alert": "System alert: Please check.",
            "Test": "This is a test message.",
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("Send SMS")
        form = QFormLayout()

        # SIM selector
        sim_layout = QHBoxLayout()
        self.sim1_radio = QRadioButton("SIM1")
        self.sim2_radio = QRadioButton("SIM2")
        self.sim1_radio.setChecked(True)
        self.sim_group = QButtonGroup(self)
        self.sim_group.addButton(self.sim1_radio, 1)
        self.sim_group.addButton(self.sim2_radio, 2)
        sim_layout.addWidget(self.sim1_radio)
        sim_layout.addWidget(self.sim2_radio)
        form.addRow("SIM:", sim_layout)

        # Phone number
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Recipient number")
        form.addRow("Number:", self.phone_input)

        # Template selector
        self.template_combo = QComboBox()
        self.template_combo.addItem("Select template...")
        self.template_combo.addItems(self.templates.keys())
        self.template_combo.currentTextChanged.connect(self.load_template)
        form.addRow("Template:", self.template_combo)

        # Message area
        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText("Enter message")
        self.message_text.setMaximumHeight(100)
        form.addRow("Message:", self.message_text)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100)
        self.quantity_spin.setValue(1)
        form.addRow("Quantity:", self.quantity_spin)

        # Send button
        self.send_btn = QPushButton("Send SMS")
        self.send_btn.clicked.connect(self.send_sms)
        form.addRow("", self.send_btn)

        group.setLayout(form)
        layout.addWidget(group)

        # Phonebook (simple)
        phonebook_group = QGroupBox("Phonebook")
        phonebook_layout = QVBoxLayout()
        self.phonebook_combo = QComboBox()
        self.phonebook_combo.addItems(["Mom: +79161234567", "Dad: +79167654321"])
        self.use_phonebook_btn = QPushButton("Use Selected")
        self.use_phonebook_btn.clicked.connect(self.use_phonebook)
        phonebook_layout.addWidget(self.phonebook_combo)
        phonebook_layout.addWidget(self.use_phonebook_btn)
        phonebook_group.setLayout(phonebook_layout)
        layout.addWidget(phonebook_group)

        layout.addStretch()
        self.setLayout(layout)

    def load_template(self, template_name):
        if template_name in self.templates:
            self.message_text.setPlainText(self.templates[template_name])

    def use_phonebook(self):
        text = self.phonebook_combo.currentText()
        if ':' in text:
            number = text.split(':')[1].strip()
            self.phone_input.setText(number)

    def send_sms(self):
        if not self.modem.connected:
            self.logger.warning("Modem not connected")
            return

        # Ensure correct SIM is selected
        selected_sim = self.sim_group.checkedId()
        if selected_sim != self.modem.active_sim:
            self.logger.info(f"Switching to SIM{selected_sim} for SMS")
            if not self.modem.select_sim(selected_sim):
                self.logger.error("SIM switch failed")
                return

        number = self.phone_input.text().strip()
        if not number:
            self.logger.warning("Phone number is empty")
            return

        message = self.message_text.toPlainText().strip()
        if not message:
            self.logger.warning("Message is empty")
            return

        quantity = self.quantity_spin.value()
        self.logger.info(f"Sending {quantity} SMS to {number}")

        for i in range(quantity):
            success = self.modem.send_sms(number, message)
            if success:
                self.logger.info(f"SMS {i+1}/{quantity} sent")
            else:
                self.logger.error(f"SMS {i+1}/{quantity} failed")
                break

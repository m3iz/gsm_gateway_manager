"""
SMS sending panel with phonebook integration.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QRadioButton, QButtonGroup, QLineEdit,
                             QTextEdit, QSpinBox, QPushButton, QLabel,
                             QComboBox, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

from utils.phonebook import Phonebook
from gui.phonebook_dialog import PhonebookDialog

class SmsPanel(QWidget):
    def __init__(self, modem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.phonebook = Phonebook()
        self.templates = {
            "Welcome": "Welcome to our service!",
            "Alert": "System alert: Please check.",
            "Test": "This is a test message.",
            "Info": "Important information...",
            "Reminder": "Reminder: Don't forget..."
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        sms_group = QGroupBox("Send SMS")
        form = QFormLayout()
        form.setSpacing(3)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # SIM selector - horizontal
        sim_layout = QHBoxLayout()
        sim_layout.setSpacing(20)
        
        self.sim1_radio = QRadioButton("SIM 1")
        self.sim2_radio = QRadioButton("SIM 2")
        self.sim1_radio.setChecked(True)
        
        self.sim_group = QButtonGroup(self)
        self.sim_group.addButton(self.sim1_radio, 1)
        self.sim_group.addButton(self.sim2_radio, 2)
        
        sim_layout.addWidget(self.sim1_radio)
        sim_layout.addWidget(self.sim2_radio)
        sim_layout.addStretch()
        
        form.addRow("SIM:", sim_layout)

        # Phone number with phonebook
        number_layout = QHBoxLayout()
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        number_layout.addWidget(self.phone_input)
        
        self.phonebook_btn = QPushButton("📖")
        self.phonebook_btn.setFixedWidth(35)
        self.phonebook_btn.clicked.connect(self.open_phonebook)
        number_layout.addWidget(self.phonebook_btn)
        
        form.addRow("Number:", number_layout)

        # Quick contacts
        quick_layout = QHBoxLayout()
        self.quick_combo = QComboBox()
        self.quick_combo.addItem("Quick contacts...")
        self.update_quick_contacts()
        self.quick_combo.currentIndexChanged.connect(self.use_quick_contact)
        quick_layout.addWidget(self.quick_combo)
        form.addRow("Quick:", quick_layout)

        # Template
        self.template_combo = QComboBox()
        self.template_combo.addItem("Template...")
        self.template_combo.addItems(self.templates.keys())
        self.template_combo.currentTextChanged.connect(self.load_template)
        form.addRow("Template:", self.template_combo)

        # Message
        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText("Message")
        self.message_text.setMaximumHeight(80)
        self.message_text.setMinimumHeight(60)
        self.message_text.textChanged.connect(self.update_char_count)
        form.addRow("Message:", self.message_text)

        # Quantity and send
        bottom_layout = QHBoxLayout()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setFixedWidth(70)
        
        self.char_count = QLabel("0/160")
        self.char_count.setStyleSheet("color: #888;")
        
        self.send_btn = QPushButton("📨 Send")
        self.send_btn.clicked.connect(self.send_sms)
        
        bottom_layout.addWidget(QLabel("x"))
        bottom_layout.addWidget(self.quantity_spin)
        bottom_layout.addWidget(self.char_count)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.send_btn)
        
        form.addRow("", bottom_layout)

        sms_group.setLayout(form)
        layout.addWidget(sms_group)
        self.setLayout(layout)

    def update_quick_contacts(self):
        while self.quick_combo.count() > 1:
            self.quick_combo.removeItem(1)
        for contact in self.phonebook.contacts[:5]:
            self.quick_combo.addItem(f"{contact['name']}: {contact['number']}")

    def open_phonebook(self):
        dialog = PhonebookDialog(self.phonebook, self)
        dialog.contacts_updated.connect(self.update_quick_contacts)
        if dialog.exec():
            idx, contact = dialog.get_selected_contact()
            if contact:
                self.phone_input.setText(contact['number'])

    def use_quick_contact(self, index):
        if index > 0:
            text = self.quick_combo.currentText()
            if ':' in text:
                self.phone_input.setText(text.split(':')[1].strip())
            self.quick_combo.setCurrentIndex(0)

    def update_char_count(self):
        length = len(self.message_text.toPlainText())
        self.char_count.setText(f"{length}/160")
        self.char_count.setStyleSheet("color: #ff5555;" if length > 160 else "color: #888;")

    def load_template(self, template_name):
        if template_name in self.templates:
            self.message_text.setPlainText(self.templates[template_name])

    def send_sms(self):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            QMessageBox.warning(self, "Error", "Modem not connected!")
            return

        selected_sim = self.sim_group.checkedId()
        if selected_sim != self.modem.active_sim:
            if not self.modem.select_sim(selected_sim):
                QMessageBox.critical(self, "Error", "Failed to switch SIM!")
                return

        number = self.phone_input.text().strip()
        if not number:
            QMessageBox.warning(self, "Error", "Enter phone number!")
            return

        message = self.message_text.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Error", "Enter message!")
            return

        quantity = self.quantity_spin.value()
        
        if quantity > 1:
            reply = QMessageBox.question(self, "Confirm", f"Send {quantity} SMS?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

        for i in range(quantity):
            success = self.modem.send_sms(number, message)
            if success:
                self.logger.info(f"SMS {i+1}/{quantity} sent")
            else:
                self.logger.error(f"SMS {i+1}/{quantity} failed")
                QMessageBox.critical(self, "Error", f"SMS {i+1} failed!")
                break

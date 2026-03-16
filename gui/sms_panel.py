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
            "Info": "Important information: ...",
            "Reminder": "Reminder: Don't forget to..."
        }
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Основная группа SMS
        sms_group = QGroupBox("Send SMS")
        form = QFormLayout()
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # SIM selector
        sim_layout = QHBoxLayout()
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
        self.phone_input.setPlaceholderText("Enter phone number or select from phonebook")
        number_layout.addWidget(self.phone_input)
        
        self.phonebook_btn = QPushButton("📖 Phonebook")
        self.phonebook_btn.clicked.connect(self.open_phonebook)
        self.phonebook_btn.setFixedWidth(100)
        number_layout.addWidget(self.phonebook_btn)
        
        form.addRow("Number:", number_layout)

        # Quick contacts
        quick_layout = QHBoxLayout()
        self.quick_combo = QComboBox()
        self.quick_combo.addItem("Quick contacts...")
        self.update_quick_contacts()
        self.quick_combo.currentIndexChanged.connect(self.use_quick_contact)
        
        quick_layout.addWidget(self.quick_combo)
        quick_layout.addStretch()
        form.addRow("Quick:", quick_layout)

        # Template selector
        self.template_combo = QComboBox()
        self.template_combo.addItem("Select template...")
        self.template_combo.addItems(self.templates.keys())
        self.template_combo.currentTextChanged.connect(self.load_template)
        form.addRow("Template:", self.template_combo)

        # Message area
        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText("Enter message text")
        self.message_text.setMaximumHeight(100)
        self.message_text.setMinimumHeight(60)
        self.message_text.textChanged.connect(self.update_char_count)
        form.addRow("Message:", self.message_text)

        # Bottom row with quantity, char count and send button
        bottom_layout = QHBoxLayout()
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setPrefix("x ")
        self.quantity_spin.setFixedWidth(80)
        
        self.char_count = QLabel("0/160")
        self.char_count.setStyleSheet("color: #888;")
        
        self.send_btn = QPushButton("📨 Send SMS")
        self.send_btn.clicked.connect(self.send_sms)
        self.send_btn.setMinimumWidth(150)
        
        bottom_layout.addWidget(QLabel("Quantity:"))
        bottom_layout.addWidget(self.quantity_spin)
        bottom_layout.addWidget(self.char_count)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.send_btn)
        
        form.addRow("", bottom_layout)

        sms_group.setLayout(form)
        main_layout.addWidget(sms_group)
        
        main_layout.addStretch()
        self.setLayout(main_layout)

    def update_quick_contacts(self):
        """Update quick contacts combo box."""
        # Keep the first item
        while self.quick_combo.count() > 1:
            self.quick_combo.removeItem(1)
        
        # Add first 5 contacts as quick access
        for contact in self.phonebook.contacts[:5]:
            self.quick_combo.addItem(f"{contact['name']}: {contact['number']}")

    def open_phonebook(self):
        """Open phonebook management dialog."""
        dialog = PhonebookDialog(self.phonebook, self)
        dialog.contacts_updated.connect(self.on_phonebook_updated)
        if dialog.exec():
            # If a contact was selected in dialog, use it
            selected = dialog.table.currentRow()
            if selected >= 0:
                # Get the actual contact from filtered view
                idx, contact = dialog.get_selected_contact()
                if contact:
                    self.phone_input.setText(contact['number'])
                    self.logger.info(f"Selected contact: {contact['name']}")

    def on_phonebook_updated(self):
        """Handle phonebook updates."""
        self.update_quick_contacts()

    def use_quick_contact(self, index):
        """Use selected quick contact."""
        if index > 0:  # Skip first "Quick contacts..." item
            text = self.quick_combo.currentText()
            if ':' in text:
                number = text.split(':')[1].strip()
                self.phone_input.setText(number)
            # Reset to first item
            self.quick_combo.setCurrentIndex(0)

    def update_char_count(self):
        text = self.message_text.toPlainText()
        length = len(text)
        self.char_count.setText(f"{length}/160")
        if length > 160:
            self.char_count.setStyleSheet("color: #ff5555;")
        else:
            self.char_count.setStyleSheet("color: #888;")

    def load_template(self, template_name):
        if template_name in self.templates:
            self.message_text.setPlainText(self.templates[template_name])

    def send_sms(self):
        if not self.modem.connected:
            self.logger.warning("Modem not connected")
            QMessageBox.warning(self, "Not Connected", "Modem is not connected!")
            return

        # Ensure correct SIM is selected
        selected_sim = self.sim_group.checkedId()
        if selected_sim != self.modem.active_sim:
            self.logger.info(f"Switching to SIM{selected_sim} for SMS")
            if not self.modem.select_sim(selected_sim):
                self.logger.error("SIM switch failed")
                QMessageBox.critical(self, "Error", "Failed to switch SIM!")
                return

        number = self.phone_input.text().strip()
        if not number:
            self.logger.warning("Phone number is empty")
            QMessageBox.warning(self, "No Number", "Please enter a phone number!")
            return

        message = self.message_text.toPlainText().strip()
        if not message:
            self.logger.warning("Message is empty")
            QMessageBox.warning(self, "No Message", "Please enter a message!")
            return

        quantity = self.quantity_spin.value()
        
        # Confirm for multiple messages
        if quantity > 1:
            reply = QMessageBox.question(
                self, "Confirm Bulk Send",
                f"Send {quantity} SMS to {number}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.logger.info(f"Sending {quantity} SMS to {number}")

        for i in range(quantity):
            success = self.modem.send_sms(number, message)
            if success:
                self.logger.info(f"SMS {i+1}/{quantity} sent")
            else:
                self.logger.error(f"SMS {i+1}/{quantity} failed")
                QMessageBox.critical(self, "Error", f"SMS {i+1} failed!")
                break

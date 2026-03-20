"""
IMEI panel for displaying and managing modem IMEI.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLineEdit, QPushButton, QLabel, QFormLayout,
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
import random

class ImeiPanel(QWidget):
    imei_changed = pyqtSignal(str)
    
    def __init__(self, modem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.current_imei = "Unknown"
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        group = QGroupBox("IMEI Configuration")
        form_layout = QFormLayout()
        form_layout.setSpacing(5)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Current IMEI display - Unknown in RED, Not connected also RED
        self.current_imei_label = QLabel(self.current_imei)
        self.current_imei_label.setStyleSheet("color: #ff5555; font-family: monospace; font-size: 10pt; font-weight: bold;")
        self.current_imei_label.setWordWrap(True)
        form_layout.addRow("Current IMEI:", self.current_imei_label)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Read IMEI")
        self.refresh_btn.clicked.connect(self.read_imei)
        self.refresh_btn.setMinimumWidth(120)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        form_layout.addRow("", refresh_layout)
        
        # New IMEI input
        self.new_imei_input = QLineEdit()
        self.new_imei_input.setPlaceholderText("Enter 15-digit IMEI")
        self.new_imei_input.setMaxLength(15)
        self.new_imei_input.setMinimumWidth(200)
        self.new_imei_input.setStyleSheet("font-family: monospace;")
        form_layout.addRow("New IMEI:", self.new_imei_input)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎲 Generate IMEI")
        self.generate_btn.clicked.connect(self.generate_imei)
        self.generate_btn.setMinimumWidth(120)
        
        self.set_btn = QPushButton("Set IMEI")
        self.set_btn.clicked.connect(self.set_imei)
        self.set_btn.setMinimumWidth(100)
        
        buttons_layout.addWidget(self.generate_btn)
        buttons_layout.addWidget(self.set_btn)
        buttons_layout.addStretch()
        
        form_layout.addRow("", buttons_layout)
        
        # Warning label
        warning_label = QLabel("⚠️ Changing IMEI may be illegal in some countries!")
        warning_label.setStyleSheet("color: #ff9900; font-size: 8pt;")
        warning_label.setWordWrap(True)
        form_layout.addRow("", warning_label)
        
        group.setLayout(form_layout)
        layout.addWidget(group)
        
        # Command status
        status_group = QGroupBox("Command Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Infinite progress
        self.progress_bar.hide()
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Auto-read IMEI if connected
        if self.modem.connected:
            QTimer.singleShot(1000, self.read_imei)
    
    def read_imei(self):
        """Read IMEI from modem using AT command."""
        if not self.modem.connected:
            self.current_imei_label.setText("Not connected")
            self.current_imei_label.setStyleSheet("color: #ff5555; font-family: monospace; font-weight: bold;")  # RED error
            self.status_label.setText("Cannot read: modem not connected")
            self.status_label.setStyleSheet("color: #ff5555;")
            return
        
        self.status_label.setText("Reading IMEI...")
        self.status_label.setStyleSheet("color: #888;")
        self.progress_bar.show()
        
        # Try different IMEI commands
        imei_commands = [
            "AT+GSN",      # Generic
            "AT+CGSN",     # Generic
            "AT+IMEI",     # Some modules
            "AT+SIM"       # Some modules
        ]
        
        for cmd in imei_commands:
            self.logger.tx(cmd)
            resp = self.modem.serial.send_command(cmd, timeout=3)
            
            for line in resp:
                self.logger.rx(line)
                # Look for IMEI (15 digits)
                if line and len(line.strip()) == 15 and line.strip().isdigit():
                    self.current_imei = line.strip()
                    self.current_imei_label.setText(self.current_imei)
                    self.current_imei_label.setStyleSheet("color: #4CAF50; font-family: monospace; font-weight: bold;")  # Green success
                    self.status_label.setText("IMEI read successfully")
                    self.status_label.setStyleSheet("color: #4CAF50;")
                    self.progress_bar.hide()
                    self.imei_changed.emit(self.current_imei)
                    return
                # Some modems return with +CGSN: or similar
                elif '+' in line and ':' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        imei = parts[1].strip().strip('"')
                        if len(imei) == 15 and imei.isdigit():
                            self.current_imei = imei
                            self.current_imei_label.setText(self.current_imei)
                            self.current_imei_label.setStyleSheet("color: #4CAF50; font-family: monospace; font-weight: bold;")  # Green success
                            self.status_label.setText("IMEI read successfully")
                            self.status_label.setStyleSheet("color: #4CAF50;")
                            self.progress_bar.hide()
                            self.imei_changed.emit(self.current_imei)
                            return
        
        self.status_label.setText("Failed to read IMEI")
        self.status_label.setStyleSheet("color: #ff5555;")  # Red error
        self.current_imei_label.setText("Read failed")
        self.current_imei_label.setStyleSheet("color: #ff5555; font-family: monospace; font-weight: bold;")  # Red error
        self.progress_bar.hide()
        self.logger.error("Could not read IMEI from modem")
    
    def generate_imei(self):
        """Generate a valid IMEI number (15 digits with Luhn checksum)."""
        # Generate first 14 digits (TAC + SNR)
        tac = f"{random.randint(10000000, 99999999)}"
        snr = f"{random.randint(100000, 999999)}"
        
        # Combine first 14 digits
        first_14 = tac + snr
        
        # Calculate Luhn checksum for 15th digit
        def luhn_checksum(number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10
        
        checksum = luhn_checksum(int(first_14) * 10)
        luhn_digit = (10 - checksum) % 10
        
        imei = first_14 + str(luhn_digit)
        
        self.new_imei_input.setText(imei)
        self.logger.info(f"Generated valid IMEI: {imei}")
    
    def set_imei(self):
        """Set new IMEI on modem."""
        if not self.modem.connected:
            QMessageBox.warning(self, "Not Connected", "Modem is not connected!")
            return
        
        new_imei = self.new_imei_input.text().strip()
        
        if not new_imei:
            QMessageBox.warning(self, "Empty IMEI", "Please enter or generate an IMEI.")
            return
        
        # Validate IMEI format
        if len(new_imei) != 15 or not new_imei.isdigit():
            QMessageBox.warning(self, "Invalid IMEI", "IMEI must be exactly 15 digits.")
            return
        
        # Confirm with user (warning about legality)
        reply = QMessageBox.question(
            self, 
            "⚠️ Warning",
            "Changing IMEI may be illegal in your country!\n\n"
            "Are you sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.status_label.setText("Setting IMEI...")
        self.status_label.setStyleSheet("color: #888;")
        self.progress_bar.show()
        
        # Try different commands to set IMEI
        set_commands = [
            f"AT+EGMR=1,7,\"{new_imei}\"",  # Sierra Wireless/Quectel
            f"AT+CGSN=1,\"{new_imei}\"",    # Generic
            f"AT+IMEI={new_imei}",           # Some modules
            f"AT+SIM={new_imei}"              # Others
        ]
        
        success = False
        for cmd in set_commands:
            self.logger.tx(cmd)
            resp = self.modem.serial.send_command(cmd, timeout=5)
            
            for line in resp:
                self.logger.rx(line)
                if 'OK' in line:
                    success = True
                    break
            
            if success:
                break
        
        self.progress_bar.hide()
        
        if success:
            self.status_label.setText("IMEI set successfully! Rebooting...")
            self.status_label.setStyleSheet("color: #4CAF50;")
            self.logger.info(f"IMEI changed to: {new_imei}")
            
            # Some modems need reboot
            self.modem.serial.send_command("AT+CFUN=1,1", timeout=1)
            
            QMessageBox.information(
                self, 
                "Success", 
                f"IMEI set to: {new_imei}\n\nModem may need to reboot to apply changes."
            )
            
            # Re-read IMEI after a delay
            QTimer.singleShot(3000, self.read_imei)
        else:
            self.status_label.setText("Failed to set IMEI")
            self.status_label.setStyleSheet("color: #ff5555;")
            self.logger.error("Failed to set IMEI")
            QMessageBox.critical(self, "Error", "Failed to set IMEI. Command not supported?")
    
    def update_status(self):
        """Update panel when modem connects/disconnects."""
        if self.modem.connected:
            self.refresh_btn.setEnabled(True)
            self.generate_btn.setEnabled(True)
            self.set_btn.setEnabled(True)
            self.read_imei()
        else:
            self.refresh_btn.setEnabled(False)
            self.generate_btn.setEnabled(False)
            self.set_btn.setEnabled(False)
            self.current_imei_label.setText("Not connected")
            self.current_imei_label.setStyleSheet("color: #ff5555; font-family: monospace; font-weight: bold;")  # RED error
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: #ff5555;")

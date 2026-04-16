"""
Call automation panel with dialing controls.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QComboBox, QLineEdit, QSpinBox, QPushButton,
                             QLabel, QFormLayout)
from PyQt6.QtCore import Qt, QTimer

class CallPanel(QWidget):
    def __init__(self, modem, logger, stat_panel):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.stat_panel = stat_panel
        self.calling_active = False
        self.call_timer = QTimer()
        self.call_timer.timeout.connect(self.place_call)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        # Call Automation Group
        auto_group = QGroupBox("Call Automation")
        auto_layout = QFormLayout()
        auto_layout.setSpacing(3)
        auto_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        number_layout = QHBoxLayout()
        self.country_combo = QComboBox()
        # Extended country list with codes
        countries = [
            "🇷🇺 Russia +7", "🇺🇸 USA +1", "🇺🇦 Ukraine +380", "🇩🇪 Germany +49",
            "🇬🇧 UK +44", "🇫🇷 France +33", "🇮🇹 Italy +39", "🇪🇸 Spain +34",
            "🇨🇦 Canada +1", "🇦🇺 Australia +61", "🇨🇳 China +86", "🇯🇵 Japan +81",
            "🇰🇷 South Korea +82", "🇮🇳 India +91", "🇧🇷 Brazil +55", "🇲🇽 Mexico +52",
            "🇿🇦 South Africa +27", "🇦🇪 UAE +971", "🇸🇦 Saudi Arabia +966", "🇹🇷 Turkey +90",
            "🇵🇱 Poland +48", "🇳🇱 Netherlands +31", "🇸🇪 Sweden +46", "🇳🇴 Norway +47",
            "🇩🇰 Denmark +45", "🇫🇮 Finland +358", "🇨🇿 Czech +420", "🇭🇺 Hungary +36",
            "🇷🇴 Romania +40", "🇧🇬 Bulgaria +359", "🇬🇷 Greece +30", "🇵🇹 Portugal +351",
            "🇧🇪 Belgium +32", "🇨🇭 Switzerland +41", "🇦🇹 Austria +43", "🇮🇪 Ireland +353",
            "🇮🇱 Israel +972", "🇪🇬 Egypt +20", "🇳🇬 Nigeria +234", "🇰🇪 Kenya +254",
            "🇦🇷 Argentina +54", "🇨🇱 Chile +56", "🇵🇪 Peru +51", "🇻🇪 Venezuela +58",
            "🇲🇾 Malaysia +60", "🇸🇬 Singapore +65", "🇵🇭 Philippines +63", "🇻🇳 Vietnam +84",
            "🇹🇭 Thailand +66", "🇮🇩 Indonesia +62", "🇵🇰 Pakistan +92", "🇧🇩 Bangladesh +880"
        ]
        self.country_combo.addItems(countries)
        self.country_combo.setMinimumWidth(150)
        self.country_combo.setEditable(True)  # Allow custom input
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        number_layout.addWidget(self.country_combo)
        number_layout.addWidget(self.phone_input)
        auto_layout.addRow("Number:", number_layout)

        delay_layout = QHBoxLayout()
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 3600)
        self.delay_spin.setValue(5)
        self.delay_spin.setFixedWidth(80)
        self.delay_unit = QComboBox()
        self.delay_unit.addItems(["sec", "min"])
        self.delay_unit.setFixedWidth(70)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addWidget(self.delay_unit)
        delay_layout.addStretch()
        auto_layout.addRow("Delay:", delay_layout)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.toggle_calling)
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.clicked.connect(self.stop_calling)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        auto_layout.addRow("", btn_layout)

        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)

        # Manual Call Group
        manual_group = QGroupBox("Manual Call")
        manual_layout = QHBoxLayout()
        self.quick_number = QLineEdit()
        self.quick_number.setPlaceholderText("Enter number")
        self.dial_btn = QPushButton("📞 Dial")
        self.dial_btn.clicked.connect(self.manual_dial)
        self.hangup_btn = QPushButton("📴 Hang Up")
        self.hangup_btn.clicked.connect(self.modem.hangup)
        manual_layout.addWidget(self.quick_number)
        manual_layout.addWidget(self.dial_btn)
        manual_layout.addWidget(self.hangup_btn)
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

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
        self.calling_active = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.logger.info(f"Starting automated calls to {number}")
        delay = self.delay_spin.value()
        if self.delay_unit.currentText() == "min":
            delay *= 60
        self.call_timer.start(delay * 1000)
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
        self.stat_panel.increment('dial_attempts')
        success = self.modem.dial(number)
        if success:
            self.logger.info("Call initiated")
            self.stat_panel.increment('successful_calls')
            QTimer.singleShot(5000, self.modem.hangup)
        else:
            self.logger.error("Call failed")
            self.stat_panel.increment('network_errors')

    def manual_dial(self):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            return
        number = self.quick_number.text().strip()
        if number:
            self.logger.info(f"Manual dial {number}")
            self.stat_panel.increment('dial_attempts')
            success = self.modem.dial(number)
            if success:
                self.logger.info("Call initiated")
                self.stat_panel.increment('successful_calls')
                QTimer.singleShot(5000, self.modem.hangup)
            else:
                self.logger.error("Call failed")
                self.stat_panel.increment('network_errors')

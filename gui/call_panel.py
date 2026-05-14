"""
Call automation panel with dialing controls.
"""
import re
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QComboBox, QLineEdit, QSpinBox, QPushButton,
                             QLabel, QFormLayout, QCheckBox)
from PyQt6.QtCore import Qt, QTimer

class CallPanel(QWidget):
    def __init__(self, modem, logger, stat_panel):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.stat_panel = stat_panel
        self.calling_active = False
        self.aggressive = False
        self.aggressive_alerting = False
        self.call_timer = QTimer()
        self.call_timer.timeout.connect(self.place_call)
        self.init_ui()
        # Регистрируем callback для URC (только для детекта гудков)
        self.modem.serial.set_rx_callback(self.on_urc)

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
        countries = [
            "(RU) Russia +7", "(US) USA +1", "(UA) Ukraine +380", "(DE) Germany +49",
            "(GB) UK +44", "(FR) France +33", "(IT) Italy +39", "(ES) Spain +34",
            "(CA) Canada +1", "(AU) Australia +61", "(CN) China +86", "(JP) Japan +81",
            "(KR) South Korea +82", "(IN) India +91", "(BR) Brazil +55", "(MX) Mexico +52",
            "(ZA) South Africa +27", "(AE) UAE +971", "(SA) Saudi Arabia +966", "(TR) Turkey +90",
            "(PL) Poland +48", "(NL) Netherlands +31", "(SE) Sweden +46", "(NO) Norway +47",
            "(DK) Denmark +45", "(FI) Finland +358", "(CZ) Czech +420", "(HU) Hungary +36",
            "(RO) Romania +40", "(BG) Bulgaria +359", "(GR) Greece +30", "(PT) Portugal +351",
            "(BE) Belgium +32", "(CH) Switzerland +41", "(AT) Austria +43", "(IE) Ireland +353",
            "(IL) Israel +972", "(EG) Egypt +20", "(NG) Nigeria +234", "(KE) Kenya +254",
            "(AR) Argentina +54", "(CL) Chile +56", "(PE) Peru +51", "(VE) Venezuela +58",
            "(MY) Malaysia +60", "(SG) Singapore +65", "(PH) Philippines +63", "(VN) Vietnam +84",
            "(TH) Thailand +66", "(ID) Indonesia +62", "(PK) Pakistan +92", "(BD) Bangladesh +880",
            "(LV) Latvia +371", "(LT) Lithuania +370", "(EE) Estonia +372", "(BY) Belarus +375",
            "(KZ) Kazakhstan +7", "(GE) Georgia +995", "(AM) Armenia +374"
        ]
        self.country_combo.addItems(countries)
        self.country_combo.setMinimumWidth(150)
        self.country_combo.setMaxVisibleItems(10)
        self.country_combo.setEditable(True)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number")
        self.phone_input.setMinimumWidth(200)
        number_layout.addWidget(self.country_combo)
        number_layout.addWidget(self.phone_input)
        auto_layout.addRow("Number:", number_layout)

        delay_layout = QHBoxLayout()
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 3600)
        self.delay_spin.setValue(5)
        self.delay_spin.setFixedWidth(80)
        self.delay_unit = QComboBox()
        self.delay_unit.addItems(["seconds", "minutes"])
        self.delay_unit.setCurrentIndex(0)
        self.delay_unit.setFixedWidth(90)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addWidget(self.delay_unit)
        delay_layout.addStretch()
        auto_layout.addRow("Delay:", delay_layout)

        # Aggressive mode checkbox
        self.aggressive_checkbox = QCheckBox("Aggressive dialing (ignore answer, force hangup)")
        auto_layout.addRow("", self.aggressive_checkbox)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_calling)
        self.stop_btn = QPushButton("Stop")
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
        self.dial_btn = QPushButton("Dial")
        self.dial_btn.clicked.connect(self.manual_dial)
        self.hangup_btn = QPushButton("Hang Up")
        self.hangup_btn.clicked.connect(self.modem.hangup)
        manual_layout.addWidget(self.quick_number)
        manual_layout.addWidget(self.dial_btn)
        manual_layout.addWidget(self.hangup_btn)
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

        self.setLayout(layout)

    def on_urc(self, line):
        """Обработка URC для агрессивного режима (alerting)"""
        if not self.aggressive:
            return
        if "+CLCC:" in line and ",2" in line:   # alerting (ringing)
            self.aggressive_alerting = True
            self.logger.info("Aggressive mode: alerting detected, hanging up")
            self.modem.serial.send_command("ATH", timeout=1)
        elif "VOICE CALL: BEGIN" in line:
            self.aggressive_alerting = True
            self.logger.info("Aggressive mode: call initiated, hanging up")
            self.modem.serial.send_command("ATH", timeout=1)

    def start_calling(self):
        if not self.modem.connected:
            self.logger.warning("Modem not connected")
            return
        number = self.phone_input.text().strip()
        if not number:
            self.logger.warning("Please enter a phone number")
            return

        country_text = self.country_combo.currentText()
        match = re.search(r'\+?(\d+)$', country_text)
        country_code = match.group(1) if match else ""
        if country_code and not number.startswith('+'):
            full_number = f"+{country_code}{number}"
        else:
            full_number = number

        self.calling_active = True
        self.aggressive = self.aggressive_checkbox.isChecked()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.logger.info(f"Starting automated calls to {full_number}")
        # Сохраняем номер для последующих вызовов
        self.current_number = full_number
        delay = self.delay_spin.value()
        if self.delay_unit.currentText() == "minutes":
            delay *= 60
        self.call_timer.start(delay * 1000)
        # Первый звонок без задержки
        QTimer.singleShot(0, self.place_call)

    def stop_calling(self):
        self.calling_active = False
        self.call_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.logger.info("Call automation stopped")
        # Принудительно сбросить текущий вызов
        self.modem.serial.send_command("ATH", timeout=1)
        # Сброс флагов
        self.aggressive = False
        self.aggressive_alerting = False

    def place_call(self):
        if not self.calling_active:
            return
        if not self.modem.connected:
            self.stop_calling()
            return

        # Сброс перед новым вызовом
        self.modem.serial.send_command("ATH", timeout=1)

        number = getattr(self, 'current_number', None)
        if not number:
            self.logger.error("No number to call")
            self.stop_calling()
            return

        self.logger.info(f"Dialing {number}...")
        self.stat_panel.increment('dial_attempts')
        success = self.modem.dial(number)

        if self.aggressive:
            # Агрессивный режим: ждём alerting (гудки) до 30 сек
            self.aggressive_alerting = False
            self.logger.info("Aggressive mode: waiting for alerting (ringing) up to 30 sec...")
            # Запускаем таймер для проверки alerting
            self.alerting_timeout = time.time() + 30
            self.alerting_timer = QTimer()
            self.alerting_timer.timeout.connect(self.check_alerting)
            self.alerting_timer.start(200)
        else:
            # Обычный режим
            if success:
                self.logger.info("Call initiated")
                self.stat_panel.increment('successful_calls')
                QTimer.singleShot(10000, self.modem.hangup)
            else:
                self.logger.error("Call failed")
                self.stat_panel.increment('network_errors')
                self.modem.serial.send_command("ATH", timeout=1)

    def check_alerting(self):
        """Периодическая проверка по таймеру (агрессивный режим)"""
        if not self.calling_active:
            self.alerting_timer.stop()
            return
        if self.aggressive_alerting:
            self.alerting_timer.stop()
            # Продолжаем цикл после задержки
            delay = self.delay_spin.value()
            if self.delay_unit.currentText() == "minutes":
                delay *= 60
            QTimer.singleShot(delay * 1000, self.place_call)
        elif time.time() > self.alerting_timeout:
            self.alerting_timer.stop()
            self.logger.warning("Aggressive mode: no alerting within 30 sec, force hangup")
            self.modem.serial.send_command("ATH", timeout=1)
            # Продолжаем цикл
            delay = self.delay_spin.value()
            if self.delay_unit.currentText() == "minutes":
                delay *= 60
            QTimer.singleShot(delay * 1000, self.place_call)

    def manual_dial(self):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            return
        number = self.quick_number.text().strip()
        if not number:
            return
        # Получаем код страны
        country_text = self.country_combo.currentText()
        match = re.search(r'\+?(\d+)$', country_text)
        country_code = match.group(1) if match else ""
        if country_code and not number.startswith('+'):
            full_number = f"+{country_code}{number}"
        else:
            full_number = number
        self.logger.info(f"Manual dial {full_number}")
        self.stat_panel.increment('dial_attempts')
        success = self.modem.dial(full_number)
        if success:
            self.logger.info("Call initiated")
            self.stat_panel.increment('successful_calls')
            QTimer.singleShot(10000, self.modem.hangup)
        else:
            self.logger.error("Call failed")
            self.stat_panel.increment('network_errors')
            self.modem.serial.send_command("ATH", timeout=1)

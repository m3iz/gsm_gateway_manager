import time
import re
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
        self.monitor_timer = None
        self.answer_timer = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

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
        self.delay_unit.addItems(["sec", "min"])
        self.delay_unit.setFixedWidth(70)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addWidget(self.delay_unit)
        delay_layout.addStretch()
        auto_layout.addRow("Delay between calls:", delay_layout)

        # Answer timeout
        answer_layout = QHBoxLayout()
        self.answer_timeout_spin = QSpinBox()
        self.answer_timeout_spin.setRange(5, 300)
        self.answer_timeout_spin.setValue(30)
        self.answer_timeout_spin.setFixedWidth(80)
        answer_layout.addWidget(self.answer_timeout_spin)
        answer_layout.addWidget(QLabel("sec"))
        answer_layout.addStretch()
        auto_layout.addRow("Answer timeout:", answer_layout)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.toggle_calling)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_calling)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        auto_layout.addRow("", btn_layout)

        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)

        manual_group = QGroupBox("Manual Call")
        manual_layout = QHBoxLayout()
        self.quick_number = QLineEdit()
        self.quick_number.setPlaceholderText("Enter number")
        self.dial_btn = QPushButton("Dial")
        self.dial_btn.clicked.connect(self.manual_dial)
        self.hangup_btn = QPushButton("Hang Up")
        self.hangup_btn.clicked.connect(self.manual_hangup)
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
        self._stop_network_timer()
        self.place_call()

    def stop_calling(self):
        self.calling_active = False
        if self.monitor_timer and self.monitor_timer.isActive():
            self.monitor_timer.stop()
        if self.answer_timer and self.answer_timer.isActive():
            self.answer_timer.stop()
        self.call_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.logger.info("Call automation stopped")
        # Hangup any active call
        self.modem.serial.send_command("ATH", timeout=2)
        time.sleep(1)
        if self.modem.serial.port and self.modem.serial.port.is_open:
            try:
                self.modem.serial.port.reset_input_buffer()
            except:
                pass
        self._start_network_timer()

    def place_call(self):
        self._stop_waiting()
        self.call_timer.stop()
        if hasattr(self, "monitor_timer"):
            self.monitor_timer = None
        if hasattr(self, "answer_timer"):
            self.answer_timer = None
        self._stop_waiting()
        self.modem.serial.send_command("ATH", timeout=2)
        time.sleep(0.5)
        self._stop_waiting()
        self._stop_waiting()
        if not self.calling_active:
            return
        # Clean buffer and force hangup before call
        if self.modem.serial.port and self.modem.serial.port.is_open:
            try:
                self.modem.serial.port.reset_input_buffer()
            except:
                pass
        self.modem.serial.send_command("ATH", timeout=1)
        time.sleep(0.3)
        number = self.phone_input.text().strip()
        country_text = self.country_combo.currentText()
        match = re.search(r'\+?(\d+)$', country_text)
        country_code = match.group(1) if match else ""
        if country_code and not number.startswith('+'):
            full_number = f"+{country_code}{number}"
        else:
            full_number = number
        self.logger.info(f"Dialing {full_number}...")
        self.stat_panel.increment('dial_attempts')
        # Send ATD
        resp = self.modem.serial.send_command(f"ATD{full_number};", timeout=10)
        self.logger.info(f"ATD response: {resp}")
        self.logger.info(f"ATD response: {resp}")
        if not resp or not any('OK' in line for line in resp):
            self.logger.error(f"Call failed (no OK), response: {resp}")
            self.stat_panel.increment('network_errors')
            # Попытка переподключения к порту
            self.logger.info("Attempting to reconnect to modem...")
            port_name = self.modem.serial.port.port
            self.modem.disconnect()
            time.sleep(1)
            self.modem.connect(port_name, 115200)
            time.sleep(1)
            self._schedule_next()
            return
        if not any('OK' in line for line in resp):
            self.logger.error(f"Call failed (no OK), response: {resp}")
            self.stat_panel.increment('network_errors')
            self._schedule_next()
            return
        self.logger.info("Call initiated, waiting for answer...")
        # Start answer timeout timer
        timeout_sec = self.answer_timeout_spin.value()
        self.answer_timer = QTimer()
        self.answer_timer.setSingleShot(True)
        self.answer_timer.timeout.connect(self._answer_timeout)
        self.answer_timer.start(timeout_sec * 1000)
        # Start monitoring URC for connected
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_call)
        self.monitor_timer.start(300)

    def _monitor_call(self):
        if not self.calling_active:
            if self.monitor_timer:
                self.monitor_timer.stop()
            return
        if self.modem.serial.port and self.modem.serial.port.in_waiting:
            while self.modem.serial.port.in_waiting:
                line = self.modem.serial.port.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                self.logger.rx(line)
                # Detect connected (state 0)
                if '+CLCC:' in line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        state = parts[2].strip()
                        if state == '0':
                            self.logger.info("Call answered (connected)!")
                            self._stop_waiting()
                            self.stat_panel.increment('successful_calls')
                            self._stop_waiting()
                            # Hangup and wait for OK
                            ##self.modem.serial.send_command("ATH", timeout=2)
                            time.sleep(1)
                            self._schedule_next()
                            return
                # Detect early end
                if 'NO CARRIER' in line or 'BUSY' in line:
                    self.modem.serial.send_command("ATH", timeout=3)
                    time.sleep(1)
                    if self.modem.serial.port and self.modem.serial.port.is_open:
                        self.modem.serial.port.reset_input_buffer()
                    self.logger.info("Call ended before timeout (busy/no carrier)")
                    self.stat_panel.increment("rejected_calls")
                    self._stop_waiting()
                    self._schedule_next()
                    return

    def _answer_timeout(self):
        self.logger.info("Answer timeout, hanging up")
        self.logger.info(f"Current stats: {self.stat_panel.stats}")
        self.stat_panel.increment('rejected_calls')
        self._stop_waiting()  # остановить monitor_timer и answer_timer
        self.modem.serial.send_command("ATH", timeout=5)
        time.sleep(1)
        if self.modem.serial.port and self.modem.serial.port.is_open:
            self.modem.serial.port.reset_input_buffer()
        self._schedule_next()
        if not self.modem.wait_for_ready():
            self.logger.error("Modem not ready, stopping calls")
            self.stop_calling()
            return
        if self.calling_active:
            delay = self.delay_spin.value()
            if self.delay_unit.currentText() == "min":
                delay *= 60
            self.call_timer.start(delay * 1000)

    def manual_dial(self):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            return
        number = self.quick_number.text().strip()
        if number:
            if self.modem.serial.port and self.modem.serial.port.is_open:
                try:
                    self.modem.serial.port.reset_input_buffer()
                except:
                    pass
            self.logger.info(f"Manual dial {number}")
            self.stat_panel.increment('dial_attempts')
            resp = self.modem.serial.send_command(f"ATD{number};", timeout=10)
            success = any('OK' in line for line in resp)
            print(f"DEBUG dial: cmd=ATD{number};, resp={resp}, result={success}")
            if success:
                self.logger.info("Call initiated")
                self.stat_panel.increment('successful_calls')
            else:
                self.logger.error("Call failed")
                self.stat_panel.increment('network_errors')

    def manual_hangup(self):
        self.logger.info("Manual hangup")
        self.modem.serial.send_command("ATH", timeout=2)
        time.sleep(1)
        if self.modem.serial.port and self.modem.serial.port.is_open:
            try:
                self.modem.serial.port.reset_input_buffer()
            except:
                pass

    def _stop_network_timer(self):
        try:
            main_window = self.window()
            if hasattr(main_window, 'conn_panel') and hasattr(main_window.conn_panel, 'refresh_timer'):
                main_window.conn_panel.refresh_timer.stop()
        except:
            pass

    def _start_network_timer(self):
        try:
            main_window = self.window()
            if hasattr(main_window, 'conn_panel') and hasattr(main_window.conn_panel, 'refresh_timer'):
                main_window.conn_panel.refresh_timer.start(30000)
        except:
            pass

    def _answer_timeout(self):
        self.logger.info("Answer timeout, hanging up")
        self.logger.info(f"Current stats: {self.stat_panel.stats}")
        self.stat_panel.increment('rejected_calls')
        self._stop_waiting()  # остановить monitor_timer и answer_timer
        self.modem.serial.send_command("ATH", timeout=5)
        time.sleep(1)
        if self.modem.serial.port and self.modem.serial.port.is_open:
            self.modem.serial.port.reset_input_buffer()
        self._schedule_next()
        if hasattr(self, 'monitor_timer') and self.monitor_timer and self.monitor_timer.isActive():
            self.monitor_timer.stop()
        if hasattr(self, 'answer_timer') and self.answer_timer and self.answer_timer.isActive():
            self.answer_timer.stop()

    def _stop_waiting(self):
        if hasattr(self, 'monitor_timer') and self.monitor_timer and self.monitor_timer.isActive():
            self.monitor_timer.stop()
        if hasattr(self, 'answer_timer') and self.answer_timer and self.answer_timer.isActive():
            self.answer_timer.stop()

    def _schedule_next(self):
        if self.calling_active:
            self.call_timer.stop()
            delay = self.delay_spin.value()
            if self.delay_unit.currentText() == "min":
                delay *= 60
            self.logger.info(f"Scheduling next call in {delay} seconds")
            self.call_timer.start(delay * 1000)

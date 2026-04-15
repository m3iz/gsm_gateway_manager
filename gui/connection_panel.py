"""
Connection panel widget displaying modem status and controls.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QComboBox, QPushButton, QLabel, QProgressBar,
                             QGridLayout, QMessageBox, QLineEdit, QDialog,
                             QFormLayout, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

class PinDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIM PIN Required")
        self.setModal(True)
        layout = QVBoxLayout()
        form = QFormLayout()
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("Enter PIN code")
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("PIN:", self.pin_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
    def get_pin(self):
        return self.pin_input.text().strip()

class ConnectionPanel(QWidget):
    connection_changed = pyqtSignal(bool)

    def __init__(self, modem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.init_ui()
        # Таймер только для обновления сигнала и оператора (не для SIM)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_network_display)
        self.refresh_timer.start(5000)  # раз в 5 секунд
        self.refresh_ports()
        # Подписываемся на URC для мгновенного обновления статуса SIM
        self.modem.register_urc_callback(self.on_urc)

    def on_urc(self, line):
        if line.startswith("SIM_STATUS:"):
            status = line.split(":", 1)[1].strip()
            self.update_sim_ui(status)
        elif "SIM not inserted" in line:
            self.update_sim_ui("SIM NOT INSERTED")
        elif "+CPIN:" in line:
            # Принудительно перепроверим статус
            QTimer.singleShot(500, self.check_sim_and_pin)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # Connection group
        conn_group = QGroupBox("Connection")
        conn_layout = QVBoxLayout()
        port_row = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        self.refresh_ports_btn = QPushButton("↻")
        self.refresh_ports_btn.setFixedWidth(30)
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        port_row.addWidget(QLabel("Port:"))
        port_row.addWidget(self.port_combo)
        port_row.addWidget(self.refresh_ports_btn)
        port_row.addStretch()
        baud_row = QHBoxLayout()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400"])
        self.baud_combo.setCurrentText("115200")
        baud_row.addWidget(QLabel("Baudrate:"))
        baud_row.addWidget(self.baud_combo)
        baud_row.addStretch()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setMinimumHeight(30)
        conn_layout.addLayout(port_row)
        conn_layout.addLayout(baud_row)
        conn_layout.addWidget(self.connect_btn)
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # Status group
        status_group = QGroupBox("Modem Status")
        status_layout = QGridLayout()
        status_layout.setSpacing(2)
        self.conn_status = QLabel("Disconnected")
        self.conn_status.setStyleSheet("color: #ff5555; font-weight: bold;")
        self.signal_bar = QProgressBar()
        self.signal_bar.setRange(0, 100)
        self.signal_bar.setValue(0)
        self.signal_bar.setTextVisible(False)
        self.signal_bar.setFixedHeight(8)
        self.operator_label = QLabel("Unknown")
        self.cell_id_label = QLabel("Unknown")
        self.sim_status_label = QLabel("Unknown")
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff5555; font-size: 9pt;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        row = 0
        status_layout.addWidget(QLabel("Status:"), row, 0)
        status_layout.addWidget(self.conn_status, row, 1); row += 1
        status_layout.addWidget(QLabel("Signal:"), row, 0)
        status_layout.addWidget(self.signal_bar, row, 1); row += 1
        status_layout.addWidget(QLabel("Operator:"), row, 0)
        status_layout.addWidget(self.operator_label, row, 1); row += 1
        status_layout.addWidget(QLabel("Cell ID:"), row, 0)
        status_layout.addWidget(self.cell_id_label, row, 1); row += 1
        status_layout.addWidget(QLabel("SIM:"), row, 0)
        status_layout.addWidget(self.sim_status_label, row, 1); row += 1

        self.pin_btn = QPushButton("Enter PIN")
        self.pin_btn.clicked.connect(self.manual_pin_entry)
        self.pin_btn.setVisible(False)
        status_layout.addWidget(QLabel(""), row, 0)
        status_layout.addWidget(self.pin_btn, row, 1); row += 1

        status_layout.addWidget(self.error_label, row, 0, 1, 2)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Quick commands
        cmd_group = QGroupBox("Quick Commands")
        cmd_layout = QHBoxLayout()
        self.at_btn = QPushButton("AT")
        self.at_btn.clicked.connect(lambda: self.send_quick_cmd("AT"))
        self.csq_btn = QPushButton("CSQ")
        self.csq_btn.clicked.connect(lambda: self.send_quick_cmd("AT+CSQ"))
        self.cops_btn = QPushButton("COPS")
        self.cops_btn.clicked.connect(lambda: self.send_quick_cmd("AT+COPS?"))
        cmd_layout.addWidget(self.at_btn)
        cmd_layout.addWidget(self.csq_btn)
        cmd_layout.addWidget(self.cops_btn)
        cmd_group.setLayout(cmd_layout)
        layout.addWidget(cmd_group)
        self.setLayout(layout)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.modem.serial.get_available_ports()
        if ports:
            for port in ports:
                if isinstance(port, dict):
                    display = f"{port['device']} - {port.get('description', '')}" if port.get('description') else port['device']
                else:
                    display = port
                self.port_combo.addItem(display, port if isinstance(port, dict) else port)
        else:
            self.port_combo.addItem("No ports found")

    def toggle_connection(self):
        if self.modem.connected:
            self.modem.disconnect()
            self.connect_btn.setText("Connect")
            self.conn_status.setText("Disconnected")
            self.conn_status.setStyleSheet("color: #ff5555; font-weight: bold;")
            self.sim_status_label.setText("Unknown")
            self.pin_btn.setVisible(False)
            self.error_label.hide()
            self.connection_changed.emit(False)
            self.logger.info("Disconnected from modem")
        else:
            port_data = self.port_combo.currentData()
            if not port_data:
                port_text = self.port_combo.currentText()
                if "No ports" in port_text:
                    QMessageBox.warning(self, "No Ports", "No COM ports available!")
                    return
                port = port_text.split(' - ')[0]
            else:
                port = port_data if isinstance(port_data, str) else port_data.get('device', str(port_data))
            baudrate = int(self.baud_combo.currentText())
            self.logger.info(f"Connecting to {port} at {baudrate} baud...")
            self.connect_btn.setEnabled(False)
            self.connect_btn.setText("Connecting...")
            QTimer.singleShot(100, lambda: self._do_connect(port, baudrate))

    def _do_connect(self, port, baudrate):
        success = self.modem.connect(port, baudrate)
        if success:
            self.connect_btn.setText("Disconnect")
            self.conn_status.setText("Connected")
            self.conn_status.setStyleSheet("color: #55ff55; font-weight: bold;")
            self.error_label.hide()
            self.connection_changed.emit(True)
            self.logger.info(f"Connected to {port}")
            self.check_sim_and_pin()  # однократная проверка после подключения
            self.update_network_display()
        else:
            self.connect_btn.setText("Connect")
            error_msg = getattr(self.modem, 'last_error', 'Unknown error')
            self.conn_status.setText("Failed")
            self.error_label.setText(f"Error: {error_msg}")
            self.error_label.show()
            self.logger.error(f"Connection failed: {error_msg}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to {port}\n\nError: {error_msg}")
        self.connect_btn.setEnabled(True)

    def check_sim_and_pin(self):
        """Однократная проверка статуса SIM (по запросу)."""
        status = self.modem.check_sim_status()
        self.logger.info(f"SIM status: {status}")
        self.update_sim_ui(status)

    def update_sim_ui(self, status):
        if status == "SIM PIN":
            self.sim_status_label.setText("PIN Required")
            self.sim_status_label.setStyleSheet("color: #ff9900; font-weight: bold;")
            self.pin_btn.setVisible(True)
        elif status == "READY":
            self.sim_status_label.setText("Ready")
            self.sim_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.pin_btn.setVisible(False)
        elif status == "SIM NOT INSERTED":
            self.sim_status_label.setText("Not inserted")
            self.sim_status_label.setStyleSheet("color: #ff5555; font-weight: bold;")
            self.pin_btn.setVisible(False)
        elif status.startswith("SIM PUK"):
            self.sim_status_label.setText("PUK Required")
            self.sim_status_label.setStyleSheet("color: #ff5555; font-weight: bold;")
            self.pin_btn.setVisible(False)
        else:
            self.sim_status_label.setText(status)
            self.sim_status_label.setStyleSheet("color: #888;")
            self.pin_btn.setVisible(False)

    def manual_pin_entry(self):
        dialog = PinDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pin = dialog.get_pin()
            if pin:
                self.logger.info("Sending PIN to modem...")
                success = self.modem.enter_pin(pin)
                if success:
                    self.logger.info("PIN accepted")
                    self.check_sim_and_pin()
                    QMessageBox.information(self, "PIN Accepted", "SIM card unlocked successfully.")
                    self.modem.update_network_info()
                    self.update_network_display()
                else:
                    error = getattr(self.modem, 'last_error', 'Unknown error')
                    self.logger.error(f"PIN rejected: {error}")
                    QMessageBox.critical(self, "PIN Error", f"Failed to unlock SIM: {error}")
                    self.manual_pin_entry()
            else:
                QMessageBox.warning(self, "No PIN", "Please enter a PIN code.")

    def update_network_display(self):
        """Обновление сигнала, оператора, Cell ID (без опроса SIM)."""
        if not self.modem.connected:
            return
        self.modem.update_network_info()
        self.signal_bar.setValue(self.modem.get_signal_percent())
        self.operator_label.setText(self.modem.operator[:20])
        ci = self.modem.network_info.get('ci', 'Unknown')
        self.cell_id_label.setText(str(ci)[:10])

    def send_quick_cmd(self, cmd):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            return
        self.logger.tx(cmd)
        resp = self.modem.serial.send_command(cmd)
        for line in resp:
            self.logger.rx(line)

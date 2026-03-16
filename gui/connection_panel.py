"""
Connection panel widget displaying modem status and controls.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QComboBox, QPushButton, QLabel, QProgressBar,
                             QGridLayout, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from gsm.gsm_modem import GsmModem

class ConnectionPanel(QWidget):
    connection_changed = pyqtSignal(bool)

    def __init__(self, modem: GsmModem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.init_ui()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_status)
        self.refresh_timer.start(5000)  # Update every 5 sec

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Connection group
        conn_group = QGroupBox("Connection")
        conn_layout = QGridLayout()

        self.port_combo = QComboBox()
        self.refresh_ports_btn = QPushButton("⟲")
        self.refresh_ports_btn.setFixedWidth(30)
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        conn_layout.addWidget(QLabel("COM Port:"), 0, 0)
        conn_layout.addWidget(self.port_combo, 0, 1)
        conn_layout.addWidget(self.refresh_ports_btn, 0, 2)
        conn_layout.addWidget(self.connect_btn, 0, 3)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        # Status group
        status_group = QGroupBox("Modem Status")
        status_layout = QGridLayout()

        self.conn_status = QLabel("Disconnected")
        self.conn_status.setStyleSheet("color: #ff5555;")
        self.signal_bar = QProgressBar()
        self.signal_bar.setRange(0, 100)
        self.signal_bar.setValue(0)
        self.signal_bar.setTextVisible(False)
        self.signal_bar.setFixedHeight(10)

        self.operator_label = QLabel("Unknown")
        self.cell_id_label = QLabel("Unknown")
        self.lac_label = QLabel("Unknown")
        self.bts_label = QLabel("Unknown")
        self.sim_status = QLabel("Unknown")
        self.network_mode = QLabel("Unknown")

        status_layout.addWidget(QLabel("Status:"), 0, 0)
        status_layout.addWidget(self.conn_status, 0, 1)
        status_layout.addWidget(QLabel("pyqtSignal:"), 1, 0)
        status_layout.addWidget(self.signal_bar, 1, 1)
        status_layout.addWidget(QLabel("Operator:"), 2, 0)
        status_layout.addWidget(self.operator_label, 2, 1)
        status_layout.addWidget(QLabel("Cell ID:"), 3, 0)
        status_layout.addWidget(self.cell_id_label, 3, 1)
        status_layout.addWidget(QLabel("LAC:"), 4, 0)
        status_layout.addWidget(self.lac_label, 4, 1)
        status_layout.addWidget(QLabel("BTS:"), 5, 0)
        status_layout.addWidget(self.bts_label, 5, 1)
        status_layout.addWidget(QLabel("SIM Status:"), 6, 0)
        status_layout.addWidget(self.sim_status, 6, 1)
        status_layout.addWidget(QLabel("Network Mode:"), 7, 0)
        status_layout.addWidget(self.network_mode, 7, 1)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Command shortcuts
        cmd_group = QGroupBox("Quick Commands")
        cmd_layout = QHBoxLayout()
        self.at_btn = QPushButton("AT")
        self.at_btn.clicked.connect(lambda: self.send_quick_cmd("AT"))
        self.csq_btn = QPushButton("AT+CSQ")
        self.csq_btn.clicked.connect(lambda: self.send_quick_cmd("AT+CSQ"))
        self.cops_btn = QPushButton("AT+COPS?")
        self.cops_btn.clicked.connect(lambda: self.send_quick_cmd("AT+COPS?"))
        cmd_layout.addWidget(self.at_btn)
        cmd_layout.addWidget(self.csq_btn)
        cmd_layout.addWidget(self.cops_btn)
        cmd_group.setLayout(cmd_layout)
        layout.addWidget(cmd_group)

        layout.addStretch()
        self.setLayout(layout)

        self.refresh_ports()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.modem.serial.get_available_ports()
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("No ports found")

    def toggle_connection(self):
        if self.modem.connected:
            self.modem.disconnect()
            self.connect_btn.setText("Connect")
            self.conn_status.setText("Disconnected")
            self.conn_status.setStyleSheet("color: #ff5555;")
            self.connection_changed.emit(False)
            self.logger.info("Disconnected from modem")
        else:
            port = self.port_combo.currentText()
            if port and "No ports" not in port:
                success = self.modem.connect(port)
                if success:
                    self.connect_btn.setText("Disconnect")
                    self.conn_status.setText("Connected")
                    self.conn_status.setStyleSheet("color: #55ff55;")
                    self.connection_changed.emit(True)
                    self.logger.info(f"Connected to {port}")
                    self.update_status()
                else:
                    self.logger.error("Connection failed")
                    # Keep disconnected state

    def update_status(self):
        if not self.modem.connected:
            return

        self.modem.update_network_info()
        self.signal_bar.setValue(self.modem.get_signal_percent())
        self.operator_label.setText(self.modem.operator)

        ci = self.modem.network_info.get('ci', 'Unknown')
        lac = self.modem.network_info.get('lac', 'Unknown')
        self.cell_id_label.setText(ci)
        self.lac_label.setText(lac)
        # BTS could be derived from cell ID, but not implemented
        self.bts_label.setText("-")
        self.sim_status.setText(f"SIM{self.modem.active_sim} Active")
        # Network mode could be from AT+CPSI? Not implemented
        self.network_mode.setText("LTE")  # Placeholder

    def send_quick_cmd(self, cmd):
        if not self.modem.connected:
            self.logger.warning("Not connected")
            return
        self.logger.tx(cmd)
        resp = self.modem.serial.send_command(cmd)
        for line in resp:
            self.logger.rx(line)

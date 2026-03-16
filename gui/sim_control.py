"""
SIM selection panel with radio buttons and auto failover option.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox,
                             QRadioButton, QButtonGroup, QCheckBox)
from PyQt6.QtCore import pyqtSignal
from gsm.gsm_modem import GsmModem

class SimControlPanel(QWidget):
    sim_changed = pyqtSignal(int)

    def __init__(self, modem: GsmModem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("SIM Control")
        group_layout = QVBoxLayout()

        self.sim1_radio = QRadioButton("SIM 1")
        self.sim2_radio = QRadioButton("SIM 2")
        self.sim1_radio.setChecked(True)  # Default

        self.sim_group = QButtonGroup(self)
        self.sim_group.addButton(self.sim1_radio, 1)
        self.sim_group.addButton(self.sim2_radio, 2)
        self.sim_group.buttonClicked.connect(self.on_sim_selected)

        self.auto_failover_cb = QCheckBox("Auto SIM failover")
        self.auto_failover_cb.toggled.connect(self.on_auto_failover_toggled)

        group_layout.addWidget(self.sim1_radio)
        group_layout.addWidget(self.sim2_radio)
        group_layout.addWidget(self.auto_failover_cb)
        group.setLayout(group_layout)

        layout.addWidget(group)
        layout.addStretch()
        self.setLayout(layout)

    def on_sim_selected(self, button):
        sim = self.sim_group.id(button)
        if self.modem.connected:
            success = self.modem.select_sim(sim)
            if success:
                self.logger.info(f"Switched to SIM{sim}")
                self.sim_changed.emit(sim)
            else:
                self.logger.error(f"Failed to switch to SIM{sim}")
                # Revert radio button
                current = self.modem.active_sim
                if current == 1:
                    self.sim1_radio.setChecked(True)
                else:
                    self.sim2_radio.setChecked(True)
        else:
            # Just update internal state
            self.modem.active_sim = sim
            self.logger.info(f"Default SIM set to {sim} (not connected)")

    def on_auto_failover_toggled(self, checked):
        self.modem.auto_failover = checked
        self.logger.info(f"Auto SIM failover {'enabled' if checked else 'disabled'}")

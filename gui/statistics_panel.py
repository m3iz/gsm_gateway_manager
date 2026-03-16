"""
Statistics panel displaying call and SMS metrics.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton)
from PyQt6.QtCore import QTimer

class StatisticsPanel(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.stats = {
            'dial_attempts': 0,
            'successful_calls': 0,
            'rejected_calls': 0,
            'network_errors': 0,
            'sms_sent': 0
        }
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("Statistics")
        grid = QGridLayout()

        self.labels = {}
        row = 0
        for key, display_name in [
            ('dial_attempts', 'Dial Attempts:'),
            ('successful_calls', 'Successful Calls:'),
            ('rejected_calls', 'Rejected Calls:'),
            ('network_errors', 'Network Errors:'),
            ('sms_sent', 'SMS Sent:')
        ]:
            grid.addWidget(QLabel(display_name), row, 0)
            self.labels[key] = QLabel("0")
            grid.addWidget(self.labels[key], row, 1)
            row += 1

        group.setLayout(grid)
        layout.addWidget(group)

        # Reset button
        self.reset_btn = QPushButton("Reset Statistics")
        self.reset_btn.clicked.connect(self.reset_stats)
        layout.addWidget(self.reset_btn)

        layout.addStretch()
        self.setLayout(layout)

    def update_display(self):
        for key, label in self.labels.items():
            label.setText(str(self.stats[key]))

    def increment(self, key):
        if key in self.stats:
            self.stats[key] += 1

    def reset_stats(self):
        for key in self.stats:
            self.stats[key] = 0
        self.logger.info("Statistics reset")

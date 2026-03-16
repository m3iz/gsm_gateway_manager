"""
Signal graph for real-time signal strength monitoring.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
import numpy as np

class SignalGraph(QWidget):
    def __init__(self, modem, logger):
        super().__init__()
        self.modem = modem
        self.logger = logger
        self.data = [0] * 60  # Last 60 samples
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)  # Update every second

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.plot_widget = pg.PlotWidget(title="Signal Strength (RSSI %)")
        self.plot_widget.setLabel('left', 'Signal %')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.showGrid(x=True, y=True)

        self.curve = self.plot_widget.plot(self.data, pen=pg.mkPen(color='g', width=2))

        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def update_graph(self):
        if self.modem.connected:
            val = self.modem.get_signal_percent()
        else:
            val = 0
        self.data.pop(0)
        self.data.append(val)
        self.curve.setData(self.data)

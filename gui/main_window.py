"""
Main window organizing all panels.
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QSplitter,
                             QStatusBar, QMenuBar, QMenu, QMessageBox,
                             QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QScreen

from gsm.gsm_modem import GsmModem
from utils.logger import Logger
from .connection_panel import ConnectionPanel
from .sim_control import SimControlPanel
from .call_panel import CallPanel
from .sms_panel import SmsPanel
from .scheduler_panel import SchedulerPanel
from .statistics_panel import StatisticsPanel
from .at_console import ATConsole
# from .signal_graph import SignalGraph  # Отключено
from .log_widget import LogWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GSM Modem Manager")
        
        # Получаем размер экрана
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Устанавливаем размер окна (80% от экрана)
        self.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        
        # Центрируем окно
        self.move(
            int((screen.width() - self.width()) / 2),
            int((screen.height() - self.height()) / 2)
        )

        # Core components
        self.logger = Logger()
        self.modem = GsmModem()

        # Setup UI
        self.setup_menus()
        self.setup_central()
        self.setup_statusbar()

        # Connect logger to log widget
        self.logger.add_handler(self.log_widget.append_log)

    def setup_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        # Could add show/hide panels

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_central(self):
        central = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        central.setLayout(main_layout)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        self.conn_panel = ConnectionPanel(self.modem, self.logger)
        self.sim_panel = SimControlPanel(self.modem, self.logger)
        self.call_panel = CallPanel(self.modem, self.logger)
        self.sms_panel = SmsPanel(self.modem, self.logger)
        self.scheduler_panel = SchedulerPanel(self.logger, self.call_panel, self.sms_panel)

        left_layout.addWidget(self.conn_panel)
        left_layout.addWidget(self.sim_panel)
        left_layout.addWidget(self.call_panel)
        left_layout.addWidget(self.sms_panel)
        left_layout.addWidget(self.scheduler_panel)
        left_layout.addStretch()

        left_panel.setLayout(left_layout)

        # Right panel
        right_tabs = QTabWidget()
        self.stat_panel = StatisticsPanel(self.logger)
        self.at_console = ATConsole(self.modem, self.logger)
        # self.signal_graph = SignalGraph(self.modem, self.logger)
        self.log_widget = LogWidget()

        right_tabs.addTab(self.stat_panel, "Statistics")
        right_tabs.addTab(self.at_console, "AT Console")
        # right_tabs.addTab(self.signal_graph, "Signal Graph")
        right_tabs.addTab(self.log_widget, "Event Log")

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_tabs)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)
        self.setCentralWidget(central)

    def setup_statusbar(self):
        self.statusBar().showMessage("Ready")

    def show_about(self):
        QMessageBox.about(self, "About GSM Modem Manager",
                          "GSM Modem Manager v1.0\n"
                          "A professional tool for testing and automation of GSM modems.\n"
                          "Developed with PyQt6 and pyserial.")

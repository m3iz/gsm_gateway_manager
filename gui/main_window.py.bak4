"""
Main window organizing all panels.
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QSplitter,
                             QStatusBar, QMenuBar, QMenu, QMessageBox,
                             QApplication, QScrollArea)
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
# from .signal_graph import SignalGraph  # Временно отключено
from .log_widget import LogWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GSM Modem Manager")
        
        # Получаем размер экрана
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Устанавливаем размер окна (85% от экрана)
        self.resize(int(screen.width() * 0.85), int(screen.height() * 0.85))
        
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

        # Левая панель с прокруткой
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(3)

        # Создаем панели
        self.conn_panel = ConnectionPanel(self.modem, self.logger)
        self.sim_panel = SimControlPanel(self.modem, self.logger)
        self.call_panel = CallPanel(self.modem, self.logger)
        self.sms_panel = SmsPanel(self.modem, self.logger)
        self.scheduler_panel = SchedulerPanel(self.logger, self.call_panel, self.sms_panel)

        # Добавляем панели
        left_layout.addWidget(self.conn_panel)
        left_layout.addWidget(self.sim_panel)
        left_layout.addWidget(self.call_panel)
        left_layout.addWidget(self.sms_panel)
        left_layout.addWidget(self.scheduler_panel)
        left_layout.addStretch()

        left_panel.setLayout(left_layout)
        left_scroll.setWidget(left_panel)

        # Правая панель с вкладками
        right_tabs = QTabWidget()
        self.stat_panel = StatisticsPanel(self.logger)
        self.at_console = ATConsole(self.modem, self.logger)
        # self.signal_graph = SignalGraph(self.modem, self.logger)  # Отключено
        self.log_widget = LogWidget()

        right_tabs.addTab(self.stat_panel, "📊 Statistics")
        right_tabs.addTab(self.at_console, "💻 AT Console")
        # right_tabs.addTab(self.signal_graph, "📈 Signal Graph")  # Отключено
        right_tabs.addTab(self.log_widget, "📝 Event Log")

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_scroll)
        splitter.addWidget(right_tabs)
        
        # Устанавливаем пропорции (35% левая, 65% правая)
        total_width = self.width()
        splitter.setSizes([int(total_width * 0.35), int(total_width * 0.65)])

        main_layout.addWidget(splitter)
        self.setCentralWidget(central)

    def setup_statusbar(self):
        self.statusBar().showMessage("Ready")

    def show_about(self):
        QMessageBox.about(self, "About GSM Modem Manager",
                          "GSM Modem Manager v1.0\n"
                          "A professional tool for testing and automation of GSM modems.\n\n"
                          "Features:\n"
                          "• AT command console\n"
                          "• Call automation\n"
                          "• SMS campaigns\n"
                          "• Network monitoring\n"
                          "• Task scheduling\n\n"
                          "Developed with PyQt6 and pyserial")

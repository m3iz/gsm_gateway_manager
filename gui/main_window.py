"""
Main window with horizontal top toolbar and bottom console/logs.
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QSplitter, QStatusBar, QMenuBar,
                             QMenu, QMessageBox, QApplication, QScrollArea,
                             QFrame, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from gsm.gsm_modem import GsmModem
from utils.logger import Logger
from .connection_panel import ConnectionPanel
from .sim_control import SimControlPanel
from .imei_panel import ImeiPanel
from .call_panel import CallPanel
from .sms_panel import SmsPanel
from .scheduler_panel import SchedulerPanel
from .statistics_panel import StatisticsPanel
from .at_console import ATConsole
from .log_widget import LogWidget
from .logo import get_pixmap_from_base64, LOGO_BASE64

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
        fullscreen_action = QAction("Full Screen (F11)", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def setup_central(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        central.setLayout(main_layout)

        # ========== TOP PANEL (Horizontal toolbar with logo and all panels) ==========
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        
        # Add logo
        logo_label = QLabel()
        pixmap = get_pixmap_from_base64(LOGO_BASE64)
        logo_label.setPixmap(pixmap.scaled(48, 48, 
                                           Qt.AspectRatioMode.KeepAspectRatio, 
                                           Qt.TransformationMode.SmoothTransformation))
        top_layout.addWidget(logo_label)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        top_layout.addWidget(separator)
        
        # Create all panels in horizontal layout
        self.conn_panel = ConnectionPanel(self.modem, self.logger)
        self.sim_panel = SimControlPanel(self.modem, self.logger)
        self.imei_panel = ImeiPanel(self.modem, self.logger)
        self.call_panel = CallPanel(self.modem, self.logger)
        self.sms_panel = SmsPanel(self.modem, self.logger)
        self.scheduler_panel = SchedulerPanel(self.logger, self.call_panel, self.sms_panel)
        
        # Add all panels horizontally
        top_layout.addWidget(self.conn_panel)
        top_layout.addWidget(self.sim_panel)
        top_layout.addWidget(self.imei_panel)
        top_layout.addWidget(self.call_panel)
        top_layout.addWidget(self.sms_panel)
        top_layout.addWidget(self.scheduler_panel)
        top_layout.addStretch()
        
        # ========== BOTTOM SECTION (Statistics + Console/Logs) ==========
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)
        
        # Statistics at the top of bottom section
        self.stat_panel = StatisticsPanel(self.logger)
        bottom_layout.addWidget(self.stat_panel)
        
        # Splitter for AT Console and Log Widget (horizontal)
        console_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.at_console = ATConsole(self.modem, self.logger)
        self.log_widget = LogWidget()
        
        console_splitter.addWidget(self.at_console)
        console_splitter.addWidget(self.log_widget)
        console_splitter.setSizes([int(self.width() * 0.5), int(self.width() * 0.5)])
        
        bottom_layout.addWidget(console_splitter)
        
        # Set proportions: Statistics 30%, Console+Log 70%
        bottom_layout.setStretchFactor(self.stat_panel, 3)
        bottom_layout.setStretchFactor(console_splitter, 7)
        
        # ========== MAIN SPLITTER (Top/Bottom) ==========
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_panel)
        main_splitter.addWidget(bottom_panel)
        main_splitter.setSizes([int(self.height() * 0.45), int(self.height() * 0.55)])
        
        main_layout.addWidget(main_splitter)
        self.setCentralWidget(central)

    def setup_statusbar(self):
        self.statusBar().showMessage("Ready")

    def show_about(self):
        QMessageBox.about(self, "About GSM Modem Manager",
                          "GSM Modem Manager v1.0\n"
                          "Professional tool for GSM modem testing and automation.\n\n"
                          "Layout: Logo + all controls in horizontal toolbar at the top,\n"
                          "statistics in the middle, console and logs at the bottom.\n\n"
                          "Features:\n"
                          "• AT command console\n"
                          "• Call automation\n"
                          "• SMS campaigns\n"
                          "• Network monitoring\n"
                          "• Task scheduling\n"
                          "• IMEI management\n\n"
                          "Developed with PyQt6 and pyserial")

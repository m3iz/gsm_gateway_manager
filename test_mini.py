import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from gui.statistics_panel import StatisticsPanel
from utils.logger import Logger

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test")
        self.setGeometry(100, 100, 400, 300)
        
        logger = Logger()
        central = QWidget()
        layout = QVBoxLayout()
        
        # Пробуем создать панель статистики
        stat_panel = StatisticsPanel(logger)
        layout.addWidget(stat_panel)
        
        central.setLayout(layout)
        self.setCentralWidget(central)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

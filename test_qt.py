#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Test Window")
    window.setGeometry(100, 100, 300, 200)
    label = QLabel("PyQt6 работает!")
    window.setCentralWidget(label)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

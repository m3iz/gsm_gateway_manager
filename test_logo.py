import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt
from gui.logo import get_pixmap_from_base64, LOGO_BASE64

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Logo")
        self.setGeometry(100, 100, 800, 600)
        
        # Проверяем загрузку логотипа
        pixmap = get_pixmap_from_base64(LOGO_BASE64)
        print(f"Логотип загружен: {not pixmap.isNull()}")
        print(f"Размер логотипа: {pixmap.width()}x{pixmap.height()}")
        
        # Показываем логотип в центре для проверки
        label = QLabel(self)
        label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
        label.move(300, 200)
        label.show()

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

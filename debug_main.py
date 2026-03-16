#!/usr/bin/env python3
import sys
import traceback
from PyQt6.QtWidgets import QApplication

def debug_import(module_name):
    try:
        print(f"Импортируем {module_name}...")
        module = __import__(module_name)
        print(f"  ✓ {module_name} загружен")
        return module
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        traceback.print_exc()
        return None

print("="*50)
print("Пошаговая загрузка модулей")
print("="*50)

# Загружаем модули по одному
debug_import('utils.logger')
debug_import('gsm.at_commands')
debug_import('gsm.serial_manager')
debug_import('gsm.gsm_modem')
debug_import('gui.log_widget')
debug_import('gui.connection_panel')
debug_import('gui.sim_control')
debug_import('gui.call_panel')
debug_import('gui.sms_panel')
debug_import('gui.scheduler_panel')
debug_import('gui.statistics_panel')
debug_import('gui.at_console')
debug_import('gui.signal_graph')
debug_import('gui.main_window')

print("="*50)
print("Создание QApplication")
print("="*50)

try:
    app = QApplication(sys.argv)
    print("✓ QApplication создан")
except Exception as e:
    print(f"✗ Ошибка создания QApplication: {e}")
    traceback.print_exc()
    sys.exit(1)

print("="*50)
print("Создание MainWindow")
print("="*50)

try:
    from gui.main_window import MainWindow
    window = MainWindow()
    print("✓ MainWindow создан")
except Exception as e:
    print(f"✗ Ошибка создания MainWindow: {e}")
    traceback.print_exc()
    sys.exit(1)

print("="*50)
print("Показ окна")
print("="*50)

try:
    window.show()
    print("✓ Окно показано")
except Exception as e:
    print(f"✗ Ошибка показа окна: {e}")
    traceback.print_exc()
    sys.exit(1)

print("="*50)
print("Запуск цикла событий")
print("="*50)

sys.exit(app.exec())

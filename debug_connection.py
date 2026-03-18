#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from gsm.gsm_modem import GsmModem
from utils.logger import Logger

def debug_connect(port_name):
    print(f"\n=== Отладка подключения к {port_name} ===")
    
    modem = GsmModem()
    logger = Logger()
    
    # Логируем в консоль
    logger.add_handler(print)
    
    print("1. Пытаемся подключиться...")
    success = modem.connect(port_name, baudrate=115200)
    
    print(f"2. Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
    
    if success:
        print("3. Проверка связи:")
        resp = modem.serial.send_command("AT", timeout=2)
        print(f"   Ответ: {resp}")
        
        print("4. Отключаемся...")
        modem.disconnect()
        print("✅ Готово")
    else:
        print("3. Проверка состояния после ошибки:")
        print(f"   modem.connected = {modem.connected}")
        print(f"   modem.serial.port = {modem.serial.port}")

if __name__ == "__main__":
    # Создаем QApplication для PyQt (нужен для сигналов)
    app = QApplication(sys.argv)
    
    # Порт для тестирования - замените на ваш
    port = "/dev/ttyUSB0"  # или /dev/ttyACM0, /dev/ttyS0 и т.д.
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    debug_connect(port)

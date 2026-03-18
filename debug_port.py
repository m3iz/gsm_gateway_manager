#!/usr/bin/env python3
import serial
import serial.tools.list_ports
import time
import sys
import os
import fcntl
import termios

def test_port_detailed(port_name):
    print(f"\n{'='*50}")
    print(f"Детальное тестирование порта: {port_name}")
    print('='*50)
    
    # 1. Проверка существования
    print(f"\n1. Проверка существования:")
    if os.path.exists(port_name):
        print(f"   ✅ Порт существует")
    else:
        print(f"   ❌ Порт НЕ существует")
        return False
    
    # 2. Проверка прав доступа
    print(f"\n2. Проверка прав доступа:")
    try:
        with open(port_name, 'rb') as f:
            print(f"   ✅ Можно открыть для чтения")
    except PermissionError as e:
        print(f"   ❌ Нет прав на чтение: {e}")
        print(f"   💡 Решение: sudo chmod 666 {port_name}")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 3. Проверка, не заблокирован ли порт
    print(f"\n3. Проверка блокировки:")
    try:
        fd = os.open(port_name, os.O_RDWR | os.O_NOCTTY)
        try:
            # Попытка установить исключительную блокировку
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print(f"   ✅ Порт не заблокирован")
            fcntl.flock(fd, fcntl.LOCK_UN)
        except IOError:
            print(f"   ⚠️ Порт заблокирован другим процессом")
        finally:
            os.close(fd)
    except Exception as e:
        print(f"   ❌ Ошибка при проверке блокировки: {e}")
    
    # 4. Попытка открыть через pyserial с разными настройками
    print(f"\n4. Попытка открыть через pyserial:")
    
    baudrates = [9600, 19200, 38400, 57600, 115200, 230400]
    
    for baud in baudrates:
        print(f"\n   Тест с baudrate={baud}:")
        try:
            ser = serial.Serial(
                port=port_name,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            print(f"   ✅ Порт открыт")
            print(f"   Настройки: {baud} 8N1")
            
            # Очистка буферов
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # Отправка AT
            print(f"   Отправка AT...")
            ser.write(b'AT\r\n')
            time.sleep(0.5)
            
            # Чтение ответа
            response = b''
            timeout = time.time() + 2
            while time.time() < timeout:
                if ser.in_waiting:
                    response += ser.read(ser.in_waiting)
                else:
                    time.sleep(0.1)
            
            if response:
                print(f"   ✅ Получен ответ: {response.decode('utf-8', errors='ignore').strip()}")
            else:
                print(f"   ❌ Нет ответа")
            
            ser.close()
            print(f"   ✅ Порт закрыт")
            
        except serial.SerialException as e:
            print(f"   ❌ Ошибка: {e}")
        except Exception as e:
            print(f"   ❌ Неожиданная ошибка: {e}")
    
    return True

def list_all_ports():
    print("Доступные порты:")
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("  Нет доступных портов")
    for port in ports:
        print(f"\n  Порт: {port.device}")
        print(f"    Описание: {port.description}")
        print(f"    Производитель: {port.manufacturer}")
        print(f"    VID:PID: {port.vid:04X}:{port.pid:04X}" if port.vid else "    VID:PID: неизвестно")
        print(f"    SN: {port.serial_number}" if port.serial_number else "    SN: неизвестно")

if __name__ == "__main__":
    print("Поиск портов...")
    list_all_ports()
    
    if len(sys.argv) > 1:
        test_port_detailed(sys.argv[1])
    else:
        print("\nУкажите порт для тестирования:")
        print("  python3 debug_port.py /dev/ttyACM0")

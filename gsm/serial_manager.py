import serial
import serial.tools.list_ports
import time
from typing import Optional, List

class SerialManager:
    def __init__(self):
        self.port: Optional[serial.Serial] = None

    def get_available_ports(self) -> List[str]:
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect(self, port: str, baudrate: int = 115200, timeout: int = 2):
        try:
            self.port = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(1)
            self.port.reset_input_buffer()
            return True, f"Connected to {port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.port and self.port.is_open:
            try:
                self.port.close()
            except:
                pass
        self.port = None

    def send_command(self, command: str, timeout: float = 10) -> list:
        if not self.port or not self.port.is_open:
            return ["ERROR: Port not open"]
        try:
            # Очистка буфера с обработкой ошибок
            try:
                self.port.reset_input_buffer()
            except (OSError, serial.SerialException) as e:
                print(f"reset_input_buffer error: {e}")
                self.disconnect()
                return ["ERROR: Port error during buffer reset"]
            self.port.write((command + '\r\n').encode())
            self.port.flush()
            responses = []
            start = time.time()
            while time.time() - start < timeout:
                try:
                    if self.port.in_waiting:
                        line = self.port.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            responses.append(line)
                            if line.startswith('OK') or line.startswith('ERROR') or line.startswith('+CME ERROR'):
                                break
                    else:
                        time.sleep(0.05)
                except (OSError, serial.SerialException) as e:
                    print(f"Read error: {e}")
                    self.disconnect()
                    return [f"ERROR: {e}"]
            return responses
        except Exception as e:
            return [f"ERROR: {e}"]

    def get_device_info(self, port_name: str) -> Optional[dict]:
        """Get detailed information about a specific port."""
        for port in serial.tools.list_ports.comports():
            if port.device == port_name:
                return {
                    'device': port.device,
                    'description': port.description,
                    'manufacturer': port.manufacturer,
                    'product': port.product,
                    'vid': port.vid,
                    'pid': port.pid,
                    'serial_number': port.serial_number,
                }
        return None

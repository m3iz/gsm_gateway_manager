"""
Serial communication manager using pyserial.
Handles low-level port operations, command sending, and response reading.
"""
import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Callable

class SerialManager:
    def __init__(self):
        self.port: Optional[serial.Serial] = None
        self.rx_thread: Optional[threading.Thread] = None
        self.rx_callback: Optional[Callable[[str], None]] = None
        self.running = False
        self.lock = threading.Lock()

    def get_available_ports(self):
        """Return list of available COM ports."""
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect(self, port: str, baudrate: int = 115200, timeout: int = 1):
        """Open serial port."""
        try:
            self.port = serial.Serial(port, baudrate, timeout=timeout)
            self.running = True
            self.rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
            self.rx_thread.start()
            return True, "Connected"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        """Close serial port."""
        self.running = False
        if self.rx_thread and self.rx_thread.is_alive():
            self.rx_thread.join(timeout=2)
        if self.port and self.port.is_open:
            self.port.close()
        self.port = None

    def _rx_loop(self):
        """Background thread to read data from serial port."""
        while self.running and self.port and self.port.is_open:
            try:
                if self.port.in_waiting:
                    line = self.port.readline().decode('utf-8', errors='ignore').strip()
                    if line and self.rx_callback:
                        self.rx_callback(line)
                else:
                    time.sleep(0.01)
            except Exception:
                break

    def send_command(self, command: str, expected_response: Optional[str] = None, timeout: float = 5) -> list:
        """
        Send an AT command and wait for response.
        Returns list of response lines.
        """
        if not self.port or not self.port.is_open:
            return ["ERROR: Port not open"]

        with self.lock:
            # Clear input buffer
            self.port.reset_input_buffer()
            # Send command
            self.port.write((command + '\r\n').encode())
            self.port.flush()

            responses = []
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    line = self.port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        responses.append(line)
                        if expected_response and expected_response in line:
                            break
                        if line.startswith('OK') or line.startswith('ERROR') or line.startswith('+CME ERROR'):
                            break
                except Exception:
                    break
            return responses

    def set_rx_callback(self, callback: Callable[[str], None]):
        """Set callback for unsolicited result codes."""
        self.rx_callback = callback

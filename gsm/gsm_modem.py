"""
High-level GSM modem controller.
Uses SerialManager and provides methods for modem operations.
"""
import threading
import time
from typing import Optional, Callable, List
from .serial_manager import SerialManager
from . import at_commands as at

class GsmModem:
    def __init__(self):
        self.serial = SerialManager()
        self.connected = False
        self.active_sim = 1  # 1 or 2
        self.signal_strength = 0
        self.operator = "Unknown"
        self.network_info = {}
        self.lock = threading.Lock()
        self.rx_callbacks = []
        self.auto_failover = False

    def connect(self, port: str, baudrate: int = 115200) -> bool:
        """Connect to modem and initialize."""
        ok, msg = self.serial.connect(port, baudrate)
        if not ok:
            return False

        # Disable echo
        self.serial.send_command(at.ATE0, timeout=2)
        # Test communication
        resp = self.serial.send_command(at.AT, timeout=2)
        if any('OK' in line for line in resp):
            self.connected = True
            self.serial.set_rx_callback(self._handle_urc)
            self.update_network_info()
            return True
        else:
            self.serial.disconnect()
            return False

    def disconnect(self):
        self.serial.disconnect()
        self.connected = False

    def _handle_urc(self, line: str):
        """Handle unsolicited result codes."""
        # Notify all registered callbacks
        for cb in self.rx_callbacks:
            cb(line)

    def register_urc_callback(self, callback: Callable[[str], None]):
        self.rx_callbacks.append(callback)

    def update_network_info(self):
        """Update signal strength, operator, etc."""
        if not self.connected:
            return

        # pyqtSignal strength
        resp = self.serial.send_command(at.AT_CSQ)
        for line in resp:
            rssi = at.parse_csq(line)
            if rssi >= 0:
                self.signal_strength = rssi
                break

        # Operator
        resp = self.serial.send_command(at.AT_COPS)
        op_info = at.parse_cops(resp)
        self.operator = op_info.get('operator', 'Unknown')

        # Network registration (simplified)
        resp = self.serial.send_command(at.AT_CREG)
        for line in resp:
            if '+CREG:' in line:
                # +CREG: <n>,<stat>[,,<lac>,<ci>]
                parts = line.split(':')[1].strip().split(',')
                if len(parts) >= 5:
                    self.network_info['lac'] = parts[3].strip('"')
                    self.network_info['ci'] = parts[4].strip('"')
                break

    def select_sim(self, sim: int) -> bool:
        """
        Switch active SIM. Vendor specific.
        Example for Quectel: AT+QUICSEL=<sim>
        """
        if sim not in (1, 2):
            return False
        if not self.connected:
            return False

        resp = self.serial.send_command(f"AT+QUICSEL={sim}")
        success = any('OK' in line for line in resp)
        if success:
            self.active_sim = sim
            # Wait for network re-registration
            time.sleep(2)
            self.update_network_info()
        else:
            # If SIM switch fails and auto failover is enabled, try other SIM
            if self.auto_failover and sim == 1:
                return self.select_sim(2)
        return success

    def dial(self, number: str) -> bool:
        """Make a voice call."""
        if not self.connected:
            return False
        cmd = at.ATD.format(number)
        resp = self.serial.send_command(cmd, expected_response='OK', timeout=10)
        return any('OK' in line for line in resp)

    def hangup(self):
        """Hang up current call."""
        if self.connected:
            self.serial.send_command(at.ATH)

    def send_sms(self, number: str, text: str) -> bool:
        """Send a single SMS."""
        if not self.connected:
            return False
        # Set text mode
        self.serial.send_command(at.AT_CMGF.format(1))
        # Send command
        cmd = at.AT_CMGS.format(number)
        resp = self.serial.send_command(cmd, expected_response='>', timeout=5)
        if any('>' in line for line in resp):
            # Send message text and Ctrl+Z
            self.serial.port.write((text + '\x1A').encode())
            self.serial.port.flush()
            # Wait for final response
            time.sleep(2)
            # Could capture response
            return True
        return False

    def get_signal_percent(self) -> int:
        """Convert RSSI (0-31) to percentage."""
        rssi = self.signal_strength
        if rssi == 99 or rssi < 0:
            return 0
        # Map 0..31 to 0..100%
        return min(100, int((rssi / 31) * 100))

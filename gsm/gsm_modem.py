"""
High-level GSM modem controller.
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
        self.active_sim = 1
        self.signal_strength = 0
        self.operator = "Unknown"
        self.network_info = {}
        self.lock = threading.Lock()
        self.rx_callbacks = []
        self.auto_failover = False
        self.last_error = ""
        self.sim_status = "Unknown"

    def connect(self, port: str, baudrate: int = 115200) -> bool:
        ok, msg = self.serial.connect(port, baudrate)
        if not ok:
            self.last_error = msg
            return False

        time.sleep(1)
        for attempt in range(3):
            resp = self.serial.send_command(at.AT, timeout=3)
            if any('OK' in line for line in resp):
                self.connected = True
                self.serial.send_command(at.ATE0, timeout=2)
                self.serial.set_rx_callback(self._handle_urc)
                self.check_sim_status()
                self.update_network_info()
                return True
            time.sleep(1)
        self.serial.disconnect()
        self.last_error = "No response to AT command"
        return False

    def disconnect(self):
        self.serial.disconnect()
        self.connected = False

    def _handle_urc(self, line: str):
        if '+CPIN:' in line.upper():
            self.check_sim_status()
        elif '+CME ERROR: SIM not inserted' in line:
            self.sim_status = "SIM NOT INSERTED"
            self._notify_status()
        for cb in self.rx_callbacks:
            try:
                cb(line)
            except:
                pass

    def _notify_status(self):
        for cb in self.rx_callbacks:
            try:
                cb(f"SIM_STATUS: {self.sim_status}")
            except:
                pass

    def register_urc_callback(self, callback: Callable[[str], None]):
        self.rx_callbacks.append(callback)

    def check_sim_status(self) -> str:
        if not self.connected:
            return "Not connected"
        resp = self.serial.send_command("AT+CPIN?", timeout=3)
        for line in resp:
            if '+CPIN:' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    status = parts[1].strip()
                    self.sim_status = status
                    self._notify_status()
                    return status
            elif '+CME ERROR: SIM not inserted' in line:
                self.sim_status = "SIM NOT INSERTED"
                self._notify_status()
                return self.sim_status
        if self.sim_status == "Unknown":
            self.sim_status = "READY"
            self._notify_status()
        return self.sim_status

    def enter_pin(self, pin: str) -> bool:
        if not self.connected:
            self.last_error = "Modem not connected"
            return False
        cmd = f"AT+CPIN={pin}"
        resp = self.serial.send_command(cmd, timeout=5)
        if any('OK' in line for line in resp):
            self.check_sim_status()
            return True
        else:
            for line in resp:
                if '+CME ERROR' in line:
                    self.last_error = line
                elif 'ERROR' in line:
                    self.last_error = "Invalid PIN"
            return False

    def update_network_info(self):
        if not self.connected:
            return
        # Signal
        resp = self.serial.send_command(at.AT_CSQ)
        for line in resp:
            rssi = at.parse_csq(line)
            if rssi >= 0:
                self.signal_strength = rssi
                break
        # Operator name and code
        resp = self.serial.send_command(at.AT_COPS)
        op_info = at.parse_cops(resp)
        self.operator = op_info.get('operator', 'Unknown')
        # Try to get MCC+MNC from +COPS response
        for line in resp:
            if '+COPS:' in line:
                parts = line.split(':')[1].strip().split(',')
                if len(parts) >= 4:
                    # format 2 (numeric) gives MCC+MNC
                    if parts[1].strip() == '2' and len(parts) >= 3:
                        code = parts[2].strip('"')
                        if len(code) >= 5:
                            self.network_info['mcc'] = code[:3]
                            self.network_info['mnc'] = code[3:]
        # Registration info for LAC and CI
        resp = self.serial.send_command(at.AT_CREG)
        for line in resp:
            if '+CREG:' in line:
                parts = line.split(':')[1].strip().split(',')
                if len(parts) >= 5:
                    self.network_info['lac'] = parts[3].strip('"')
                    self.network_info['ci'] = parts[4].strip('"')

    def select_sim(self, sim: int) -> bool:
        if sim not in (1, 2):
            return False
        if not self.connected:
            return False
        commands = [
            f"AT+QUICSEL={sim}",
            f"AT+SIMSW={sim},1",
            f"AT+CSIM={sim}",
        ]
        for cmd in commands:
            resp = self.serial.send_command(cmd)
            if any('OK' in line for line in resp):
                self.active_sim = sim
                time.sleep(2)
                self.update_network_info()
                self.check_sim_status()
                return True
        return False

    def dial(self, number: str) -> bool:
        if not self.connected:
            return False
        cmd = at.ATD.format(number)
        resp = self.serial.send_command(cmd, expected_response='OK', timeout=10)
        return any('OK' in line for line in resp)

    def hangup(self):
        if self.connected:
            self.serial.send_command(at.ATH)

    def send_sms(self, number: str, text: str) -> bool:
        if not self.connected:
            return False
        self.serial.send_command(at.AT_CMGF.format(1))
        cmd = at.AT_CMGS.format(number)
        resp = self.serial.send_command(cmd, expected_response='>', timeout=5)
        if any('>' in line for line in resp):
            self.serial.port.write((text + '\x1A').encode())
            self.serial.port.flush()
            time.sleep(2)
            return True
        return False

    def get_signal_percent(self) -> int:
        rssi = self.signal_strength
        if rssi == 99 or rssi < 0:
            return 0
        return min(100, int((rssi / 31) * 100))

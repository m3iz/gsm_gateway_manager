import time
from typing import Optional
from .serial_manager import SerialManager
from . import at_commands as at

class GsmModem:
    def __init__(self, logger=None):
        self.serial = SerialManager()
        self.connected = False
        self.active_sim = 1
        self.signal_strength = 0
        self.operator = "Unknown"
        self.network_info = {}
        self.logger = None  # будет установлен из main_window
        self.last_error = ""
        self.sim_status = "Unknown"
        self.logger = logger

    def set_logger(self, logger):
        self.logger = logger

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
                self.check_sim_status()
                self.update_network_info()
                return True
            time.sleep(1)
        self.serial.disconnect()
        self.last_error = "No response to AT command"
        return False

    def disconnect(self):
        if not self.connected:
            return
        self.serial.disconnect()
        self.connected = False

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
                    return status
            elif '+CME ERROR: SIM not inserted' in line:
                self.sim_status = "SIM NOT INSERTED"
                return self.sim_status
        if self.sim_status == "Unknown":
            self.sim_status = "READY"
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
        for line in resp:
            if '+COPS:' in line:
                parts = line.split(':')[1].strip().split(',')
                if len(parts) >= 4:
                    if parts[1].strip() == '2' and len(parts) >= 3:
                        code = parts[2].strip('"')
                        if len(code) >= 5:
                            self.network_info['mcc'] = code[:3]
                            self.network_info['mnc'] = code[3:]

    def get_signal_percent(self) -> int:
        rssi = self.signal_strength
        if rssi == 99 or rssi < 0:
            return 0
        return min(100, int((rssi / 31) * 100))

    def wait_for_alerting(self, timeout=30):
        import time
        start = time.time()
        while time.time() - start < timeout:
            if not self.connected:
                return False
            if self.serial.port and self.serial.port.in_waiting:
                line = self.serial.port.readline().decode('utf-8', errors='ignore').strip()
                if '+CLCC:' in line:
                    parts = line.split(',')
                    if len(parts) >= 3 and parts[2].strip() == '3':
                        return True
                if 'VOICE CALL: BEGIN' in line:
                    return True
            else:
                time.sleep(0.1)
        return False

    def wait_for_connected(self, timeout=30):
        import time
        start = time.time()
        while time.time() - start < timeout:
            if not self.connected:
                return False
            if self.serial.port and self.serial.port.in_waiting:
                line = self.serial.port.readline().decode('utf-8', errors='ignore').strip()
                if '+CLCC:' in line:
                    parts = line.split(',')
                    if len(parts) >= 3 and parts[2].strip() == '0':
                        return True
                if 'VOICE CALL: CONNECTED' in line:
                    return True
            else:
                time.sleep(0.1)
        return False

    def is_registered(self) -> bool:
        if not self.connected:
            return False
        resp = self.serial.send_command("AT+CREG?", timeout=3)
        for line in resp:
            if '+CREG:' in line:
                parts = line.split(':')[1].strip().split(',')
                if len(parts) >= 2:
                    stat = parts[1].strip()
                    return stat in ('1', '5')
        return False

    def dial(self, number: str) -> bool:
        if not self.connected:
            return False
        cmd = at.ATD.format(number)
        resp = self.serial.send_command(cmd, timeout=10)
        return any('OK' in line for line in resp)

    def hangup(self):
        if self.connected:
            self.serial.send_command(at.ATH)

    def send_sms(self, number: str, text: str) -> bool:
        if not self.connected:
            return False
        self.serial.send_command(at.AT_CMGF.format(1), timeout=3)
        cmd = at.AT_CMGS.format(number)
        self.serial.send_command(cmd, timeout=5)
        self.serial.port.write((text + '\x1A').encode())
        self.serial.port.flush()
        time.sleep(1)
        return True

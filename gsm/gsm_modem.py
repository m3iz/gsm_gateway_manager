"""
High-level GSM modem controller.
"""
import threading
import time
from typing import Optional, Callable, List
from .serial_manager import SerialManager
from utils.logger import Logger
from . import at_commands as at

class GsmModem:
    def __init__(self):
        self.serial = SerialManager()
        self.logger = Logger()
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
                # Disable auto hangup for voice calls
                self.serial.send_command("AT+CVHU=0", timeout=2)
                self.serial.set_rx_callback(self._handle_urc)
                self.check_sim_status()
                self.update_network_info()
                return True
            time.sleep(1)
        self.serial.disconnect()
        self.connected = False
        self.last_error = "No response to AT command"
        return False

    def disconnect(self):
        self.serial.disconnect()
        self.connected = False

    def _handle_urc(self, line: str):
        """Handle unsolicited result codes."""
        if '+CPIN:' in line.upper():
            self.check_sim_status()
        elif '+CME ERROR: SIM not inserted' in line:
            self.sim_status = "SIM NOT INSERTED"
            self._notify_status()
        elif '*COPN:' in line:
            try:
                parts = line.split(',')
                if len(parts) >= 2:
                    op_name = parts[1].strip('"')
                    if op_name:
                        self.operator = op_name
                        self._notify_operator()
            except:
                pass
        elif '+CREG:' in line:
            # Parse +CREG: <stat>[,<lac>,<ci>]
            self._parse_creg(line)
        for cb in self.rx_callbacks:
            try:
                cb(line)
            except:
                pass

    def _parse_creg(self, line: str):
        """Parse +CREG response to extract LAC and Cell ID."""
        try:
            # Format: +CREG: 2,1,"456E","0007261F" or +CREG: 1,"456E","0007260B"
            parts = line.split(':')[1].strip().split(',')
            if len(parts) >= 3:
                # Mode is first param (2), then stat, then lac, then ci
                # Different modems have different formats
                if len(parts) >= 4:
                    lac_hex = parts[2].strip('"')
                    ci_hex = parts[3].strip('"')
                elif len(parts) >= 3:
                    # Sometimes format: +CREG: 1,"456E","0007260B"
                    lac_hex = parts[1].strip('"')
                    ci_hex = parts[2].strip('"')
                else:
                    return
                # Convert hex to decimal
                if lac_hex:
                    self.network_info['lac'] = str(int(lac_hex, 16))
                if ci_hex:
                    self.network_info['ci'] = str(int(ci_hex, 16))
                # self._notify_network_info()
        except Exception as e:
            print(f"Error parsing CREG: {e}")

    def _notify_network_info(self):
        """Notify UI about network info update."""
        for cb in self.rx_callbacks:
            lac = self.network_info.get('lac', 'Unknown')
            ci = self.network_info.get('ci', 'Unknown')
            cb(f"NETWORK_INFO: LAC={lac}, CI={ci}")

    def _notify_status(self):
        for cb in self.rx_callbacks:
            try:
                cb(f"SIM_STATUS: {self.sim_status}")
            except:
                pass

    def _notify_operator(self):
        for cb in self.rx_callbacks:
            try:
                cb(f"OPERATOR: {self.operator}")
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
        resp = self.serial.send_command(cmd, timeout=10)
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
        # Query CREG to get LAC and CI
        resp = self.serial.send_command("AT+CREG?", timeout=3)
        for line in resp:
            if '+CREG:' in line:
                self._parse_creg(line)

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
        """Send a single SMS without blocking UI."""
        if not self.connected:
            return False
        # Set text mode
        resp = self.serial.send_command(at.AT_CMGF.format(1), timeout=3)
        if not any('OK' in line for line in resp):
            self.logger.error("Failed to set SMS text mode")
            return False
        # Send command
        cmd = at.AT_CMGS.format(number)
        resp = self.serial.send_command(cmd, expected_response='>', timeout=10)
        if any('>' in line for line in resp):
            # Send message text and Ctrl+Z
            try:
                self.serial.port.write((text + '\x1A').encode())
                self.serial.port.flush()
                # Wait for final response
                time.sleep(0.5)
                final_resp = []
                start = time.time()
                while time.time() - start < 5:
                    if self.serial.port.in_waiting:
                        line = self.serial.port.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            final_resp.append(line)
                            if 'OK' in line or 'ERROR' in line or '+CMS ERROR' in line:
                                break
                    else:
                        time.sleep(0.05)
                return any('OK' in line for line in final_resp)
            except Exception as e:
                self.logger.error(f"SMS send error: {e}")
                return False
        else:
            self.logger.error("No '>' prompt for SMS")
            return False

    def get_signal_percent(self) -> int:
        rssi = self.signal_strength
        if rssi == 99 or rssi < 0:
            return 0
        return min(100, int((rssi / 31) * 100))

    def wait_for_call_progress(self, timeout=30):
        """Ожидает сигнал, что вызов начался (alerting/ringing). Возвращает True, если дождался."""
        if not self.connected:
            return False
        start = time.time()
        buffer = []
        while time.time() - start < timeout:
            # Читаем все накопившиеся URC
            # В синхронной версии serial_manager.py нет асинхронного чтения, 
            # поэтому проще реализовать в самом классе через send_command с ожиданием?
            # Но send_command читает только до OK/ERROR, не ловит URC.
            # Альтернатива: читать из порта напрямую, не блокируя.
            # Упростим: опрашиваем порт каждые 0.2 секунды.
            # Для этого нужно, чтобы serial_manager давал доступ к порту.
            try:
                if self.serial.port and self.serial.port.in_waiting:
                    line = self.serial.port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        if '+CLCC:' in line and ',3,' in line:  # alerting state
                            return True
                        if 'VOICE CALL: BEGIN' in line:
                            return True
                        if '+COLP' in line:  # Connected line (answered, not alerting)
                            # Но мы хотим именно alerting, а не ответ
                            # Но для агрессивного достаточно, что вызов дошёл.
                            return True
            except:
                pass
            time.sleep(0.2)
        return False

    def wait_for_ring(self, timeout=15):
        """Ждёт появления гудков (alerting) до timeout секунд. Возвращает True, если дождался."""
        if not self.serial.port or not self.serial.port.is_open:
            return False
        start = time.time()
        while time.time() - start < timeout:
            try:
                if self.serial.port.in_waiting:
                    data = self.serial.port.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        # Сохраняем в лог? Можем выводить через callback, но для простоты не будем
                        if '+CLCC:' in data and ',3,' in data:
                            return True
                        if 'VOICE CALL: BEGIN' in data:
                            return True
                        if '+COLP' in data:
                            return True
            except:
                pass
            time.sleep(0.2)
        return False

    def wait_for_ring(self, timeout=15):
        """Ждёт появления гудков (alerting) до timeout секунд. Возвращает True, если дождался."""
        if not self.serial.port or not self.serial.port.is_open:
            return False
        start = time.time()
        while time.time() - start < timeout:
            try:
                if self.serial.port.in_waiting:
                    data = self.serial.port.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        # Сохраняем в лог? Можем выводить через callback, но для простоты не будем
                        if '+CLCC:' in data and ',3,' in data:
                            return True
                        if 'VOICE CALL: BEGIN' in data:
                            return True
                        if '+COLP' in data:
                            return True
            except:
                pass
            time.sleep(0.2)
        return False

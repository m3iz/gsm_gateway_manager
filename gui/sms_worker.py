from PyQt6.QtCore import QThread, pyqtSignal
import time

class SmsWorker(QThread):
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(bool, str)  # success, error_msg
    log = pyqtSignal(str)

    def __init__(self, modem, number, message, quantity, delay):
        super().__init__()
        self.modem = modem
        self.number = number
        self.message = message
        self.quantity = quantity
        self.delay = delay

    def run(self):
        for i in range(self.quantity):
            self.progress.emit(i + 1, self.quantity)
            success = self.modem.send_sms(self.number, self.message)
            if success:
                self.log.emit(f"SMS {i+1}/{self.quantity} sent")
                if i < self.quantity - 1 and self.delay > 0:
                    time.sleep(self.delay)
            else:
                self.finished.emit(False, f"SMS {i+1} failed")
                return
        self.finished.emit(True, "")

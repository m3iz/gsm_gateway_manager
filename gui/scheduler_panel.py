"""
Scheduler panel for timed tasks.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox,
                             QDateEdit, QTimeEdit, QPushButton,
                             QComboBox, QLabel, QFormLayout, QHBoxLayout)
from PyQt6.QtCore import QDateTime, QTimer, pyqtSignal
from datetime import datetime

class SchedulerPanel(QWidget):
    def __init__(self, logger, call_panel=None, sms_panel=None):
        super().__init__()
        self.logger = logger
        self.call_panel = call_panel
        self.sms_panel = sms_panel
        self.scheduled_tasks = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_schedule)
        self.timer.start(1000)  # Check every second
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        group = QGroupBox("Schedule Task")
        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QDateTime.currentDateTime().time())

        datetime_layout = QHBoxLayout()
        datetime_layout.addWidget(self.date_edit)
        datetime_layout.addWidget(self.time_edit)

        self.task_type = QComboBox()
        self.task_type.addItems(["Start Calls", "Send SMS Campaign"])

        self.schedule_btn = QPushButton("Schedule Task")
        self.schedule_btn.clicked.connect(self.schedule_task)

        form.addRow("Date/Time:", datetime_layout)
        form.addRow("Task:", self.task_type)
        form.addRow("", self.schedule_btn)

        group.setLayout(form)
        layout.addWidget(group)

        # List of scheduled tasks (simplified)
        list_group = QGroupBox("Scheduled Tasks")
        list_layout = QVBoxLayout()
        self.task_list = QLabel("No tasks scheduled")
        list_layout.addWidget(self.task_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        layout.addStretch()
        self.setLayout(layout)

    def schedule_task(self):
        dt = self.date_edit.dateTime().toPyDateTime()
        task_type = self.task_type.currentText()
        task = {
            'datetime': dt,
            'type': task_type,
            'executed': False
        }
        self.scheduled_tasks.append(task)
        self.logger.info(f"Scheduled {task_type} at {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        self.update_task_list()

    def update_task_list(self):
        if not self.scheduled_tasks:
            self.task_list.setText("No tasks scheduled")
        else:
            text = ""
            for t in self.scheduled_tasks:
                status = "Done" if t['executed'] else "Pending"
                text += f"{t['datetime'].strftime('%Y-%m-%d %H:%M')} - {t['type']} [{status}]\n"
            self.task_list.setText(text)

    def check_schedule(self):
        now = datetime.now()
        for task in self.scheduled_tasks:
            if not task['executed'] and task['datetime'] <= now:
                self.execute_task(task)
                task['executed'] = True
        self.update_task_list()

    def execute_task(self, task):
        self.logger.info(f"Executing scheduled task: {task['type']}")
        if task['type'] == "Start Calls" and self.call_panel:
            self.call_panel.start_calling()
        elif task['type'] == "Send SMS Campaign" and self.sms_panel:
            # For demo, send SMS with current input
            self.sms_panel.send_sms()

"""
Scheduler panel for timed tasks.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QDateEdit,
                             QTimeEdit, QPushButton, QComboBox, QLabel,
                             QFormLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QMenu, QFileDialog, QMessageBox)
from PyQt6.QtCore import QDateTime, QTimer, pyqtSignal, Qt
from datetime import datetime
import json
import os

class SchedulerPanel(QWidget):
    def __init__(self, logger, call_panel=None, sms_panel=None):
        super().__init__()
        self.logger = logger
        self.call_panel = call_panel
        self.sms_panel = sms_panel
        self.scheduled_tasks = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_schedule)
        self.timer.start(1000)
        self.init_ui()
        self.load_tasks_from_file()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Schedule new task
        group = QGroupBox("Schedule New Task")
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

        # List of scheduled tasks with context menu
        list_group = QGroupBox("Scheduled Tasks")
        list_layout = QVBoxLayout()
        self.task_list = QListWidget()
        self.task_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)
        list_layout.addWidget(self.task_list)
        
        # Import/Export buttons
        btn_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import Tasks")
        self.import_btn.clicked.connect(self.import_tasks)
        self.export_btn = QPushButton("Export Tasks")
        self.export_btn.clicked.connect(self.export_tasks)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.export_btn)
        list_layout.addLayout(btn_layout)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        layout.addStretch()
        self.setLayout(layout)

    def show_context_menu(self, position):
        menu = QMenu()
        delete_action = menu.addAction("Delete Task")
        action = menu.exec(self.task_list.mapToGlobal(position))
        if action == delete_action:
            current_item = self.task_list.currentItem()
            if current_item:
                idx = self.task_list.row(current_item)
                if idx < len(self.scheduled_tasks):
                    del self.scheduled_tasks[idx]
                    self.save_tasks_to_file()
                    self.update_task_list()

    def schedule_task(self):
        dt = self.date_edit.dateTime().toPyDateTime()
        task_type = self.task_type.currentText()
        task = {
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'type': task_type,
            'executed': False
        }
        self.scheduled_tasks.append(task)
        self.save_tasks_to_file()
        self.logger.info(f"Scheduled {task_type} at {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        self.update_task_list()

    def update_task_list(self):
        self.task_list.clear()
        for task in self.scheduled_tasks:
            dt_str = task['datetime']
            status = "✓" if task['executed'] else "⏳"
            display = f"{status} {dt_str} - {task['type']}"
            self.task_list.addItem(display)

    def check_schedule(self):
        now = datetime.now()
        for task in self.scheduled_tasks:
            if not task['executed']:
                task_time = datetime.strptime(task['datetime'], '%Y-%m-%d %H:%M:%S')
                if task_time <= now:
                    self.execute_task(task)
                    task['executed'] = True
                    self.save_tasks_to_file()
                    self.update_task_list()

    def execute_task(self, task):
        self.logger.info(f"Executing scheduled task: {task['type']}")
        if task['type'] == "Start Calls" and self.call_panel:
            self.call_panel.start_calling()
        elif task['type'] == "Send SMS Campaign" and self.sms_panel:
            self.sms_panel.send_sms()

    def save_tasks_to_file(self):
        try:
            with open('scheduled_tasks.json', 'w') as f:
                json.dump(self.scheduled_tasks, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")

    def load_tasks_from_file(self):
        try:
            if os.path.exists('scheduled_tasks.json'):
                with open('scheduled_tasks.json', 'r') as f:
                    self.scheduled_tasks = json.load(f)
                self.update_task_list()
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")

    def import_tasks(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Tasks", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported = json.load(f)
                    self.scheduled_tasks.extend(imported)
                    self.save_tasks_to_file()
                    self.update_task_list()
                    self.logger.info(f"Imported {len(imported)} tasks from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import: {e}")

    def export_tasks(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Tasks", "scheduled_tasks.json", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.scheduled_tasks, f, indent=2)
                self.logger.info(f"Exported {len(self.scheduled_tasks)} tasks to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

"""
Phonebook management dialog.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit,
                             QComboBox, QLabel, QMessageBox, QFileDialog,
                             QHeaderView, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from utils.phonebook import Phonebook

class PhonebookDialog(QDialog):
    contacts_updated = pyqtSignal()
    
    def __init__(self, phonebook: Phonebook, parent=None):
        super().__init__(parent)
        self.phonebook = phonebook
        self.current_filter = "All"
        self.setWindowTitle("Phonebook Manager")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
        self.refresh_table()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_contact)
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_contact)
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_contact)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addStretch()
        
        # Search and filter
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search by name or number...")
        self.search_box.textChanged.connect(self.filter_contacts)
        
        self.group_filter = QComboBox()
        self.group_filter.addItem("All Groups")
        self.group_filter.currentTextChanged.connect(self.filter_contacts)
        
        toolbar.addWidget(QLabel("Search:"))
        toolbar.addWidget(self.search_box)
        toolbar.addWidget(QLabel("Group:"))
        toolbar.addWidget(self.group_filter)
        
        layout.addLayout(toolbar)
        
        # Contacts table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Phone Number", "Group"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_contact)
        
        layout.addWidget(self.table)
        
        # Import/Export buttons
        import_export_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("📥 Import from CSV")
        self.import_btn.clicked.connect(self.import_csv)
        self.export_btn = QPushButton("📤 Export to CSV")
        self.export_btn.clicked.connect(self.export_csv)
        
        import_export_layout.addWidget(self.import_btn)
        import_export_layout.addWidget(self.export_btn)
        import_export_layout.addStretch()
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setFixedWidth(100)
        
        import_export_layout.addWidget(self.close_btn)
        
        layout.addLayout(import_export_layout)
        
        self.setLayout(layout)
        
        # Update group filter
        self.update_group_filter()
    
    def update_group_filter(self):
        """Update group filter combo box."""
        current = self.group_filter.currentText()
        self.group_filter.clear()
        self.group_filter.addItem("All Groups")
        self.group_filter.addItems(self.phonebook.get_groups())
        
        # Restore previous selection if possible
        index = self.group_filter.findText(current)
        if index >= 0:
            self.group_filter.setCurrentIndex(index)
    
    def refresh_table(self):
        """Refresh contacts table with current filter."""
        # Apply filter
        search_text = self.search_box.text().lower()
        group = self.group_filter.currentText()
        group = None if group == "All Groups" else group
        
        contacts = self.phonebook.contacts
        if group:
            contacts = self.phonebook.get_contacts_by_group(group)
        if search_text:
            contacts = [c for c in contacts if 
                       search_text in c['name'].lower() or 
                       search_text in c['number']]
        
        self.table.setRowCount(len(contacts))
        
        for row, contact in enumerate(contacts):
            self.table.setItem(row, 0, QTableWidgetItem(contact['name']))
            self.table.setItem(row, 1, QTableWidgetItem(contact['number']))
            self.table.setItem(row, 2, QTableWidgetItem(contact['group']))
    
    def filter_contacts(self):
        """Filter contacts based on search text and group."""
        self.refresh_table()
    
    def get_selected_contact(self):
        """Get currently selected contact index and data."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None, None
        
        # Need to map back to original contacts due to filtering
        search_text = self.search_box.text().lower()
        group = self.group_filter.currentText()
        group = None if group == "All Groups" else group
        
        contacts = self.phonebook.contacts
        if group:
            contacts = self.phonebook.get_contacts_by_group(group)
        if search_text:
            contacts = [c for c in contacts if 
                       search_text in c['name'].lower() or 
                       search_text in c['number']]
        
        if current_row < len(contacts):
            contact = contacts[current_row]
            # Find original index
            for idx, c in enumerate(self.phonebook.contacts):
                if (c['name'] == contact['name'] and 
                    c['number'] == contact['number']):
                    return idx, contact
        return None, None
    
    def add_contact(self):
        """Add new contact."""
        dialog = ContactDialog(self)
        if dialog.exec():
            name, number, group = dialog.get_data()
            if self.phonebook.add_contact(name, number, group):
                self.refresh_table()
                self.update_group_filter()
                self.contacts_updated.emit()
            else:
                QMessageBox.warning(self, "Duplicate", 
                                   "This number already exists in phonebook!")
    
    def edit_contact(self):
        """Edit selected contact."""
        idx, contact = self.get_selected_contact()
        if idx is None:
            QMessageBox.information(self, "No Selection", 
                                   "Please select a contact to edit.")
            return
        
        dialog = ContactDialog(self, contact)
        if dialog.exec():
            name, number, group = dialog.get_data()
            if self.phonebook.update_contact(idx, name, number, group):
                self.refresh_table()
                self.update_group_filter()
                self.contacts_updated.emit()
    
    def delete_contact(self):
        """Delete selected contact."""
        idx, contact = self.get_selected_contact()
        if idx is None:
            QMessageBox.information(self, "No Selection", 
                                   "Please select a contact to delete.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete contact '{contact['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.phonebook.delete_contact(idx)
            self.refresh_table()
            self.update_group_filter()
            self.contacts_updated.emit()
    
    def import_csv(self):
        """Import contacts from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            count = self.phonebook.import_from_csv(file_path)
            QMessageBox.information(self, "Import Complete", 
                                   f"Imported {count} contacts.")
            self.refresh_table()
            self.update_group_filter()
            self.contacts_updated.emit()
    
    def export_csv(self):
        """Export contacts to CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "contacts.csv", "CSV Files (*.csv)"
        )
        if file_path:
            if self.phonebook.export_to_csv(file_path):
                QMessageBox.information(self, "Export Complete", 
                                       f"Exported {len(self.phonebook.contacts)} contacts.")


class ContactDialog(QDialog):
    """Dialog for adding/editing a contact."""
    
    def __init__(self, parent=None, contact=None):
        super().__init__(parent)
        self.contact = contact
        self.setWindowTitle("Edit Contact" if contact else "New Contact")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter name")
        if contact:
            self.name_edit.setText(contact['name'])
        form.addRow("Name:", self.name_edit)
        
        self.number_edit = QLineEdit()
        self.number_edit.setPlaceholderText("+79161234567")
        if contact:
            self.number_edit.setText(contact['number'])
        form.addRow("Number:", self.number_edit)
        
        self.group_edit = QLineEdit()
        self.group_edit.setPlaceholderText("Family, Work, Friends...")
        if contact:
            self.group_edit.setText(contact['group'])
        else:
            self.group_edit.setText("General")
        form.addRow("Group:", self.group_edit)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Return entered data."""
        return (
            self.name_edit.text().strip(),
            self.number_edit.text().strip(),
            self.group_edit.text().strip() or "General"
        )

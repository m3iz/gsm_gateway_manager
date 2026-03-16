"""
Phonebook manager for storing and managing contacts.
"""
import json
import os
from typing import List, Dict, Optional

class Phonebook:
    def __init__(self, filename: str = "phonebook.json"):
        """
        Initialize phonebook with JSON file storage.
        
        Args:
            filename: Path to JSON file for storing contacts
        """
        self.filename = filename
        self.contacts: List[Dict[str, str]] = []
        self.load()
    
    def load(self) -> None:
        """Load contacts from JSON file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.contacts = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading phonebook: {e}")
                self.contacts = self.get_default_contacts()
        else:
            self.contacts = self.get_default_contacts()
            self.save()
    
    def save(self) -> None:
        """Save contacts to JSON file."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.contacts, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving phonebook: {e}")
    
    def get_default_contacts(self) -> List[Dict[str, str]]:
        """Return default contacts for first run."""
        return [
            {"name": "Mom", "number": "+79161234567", "group": "Family"},
            {"name": "Dad", "number": "+79167654321", "group": "Family"},
            {"name": "Work", "number": "+74951234567", "group": "Work"},
            {"name": "Support", "number": "+78001234567", "group": "Service"}
        ]
    
    def add_contact(self, name: str, number: str, group: str = "General") -> bool:
        """
        Add new contact to phonebook.
        
        Returns:
            bool: True if added successfully, False if duplicate
        """
        # Check for duplicates
        for contact in self.contacts:
            if contact['number'] == number:
                return False
        
        self.contacts.append({
            "name": name,
            "number": number,
            "group": group
        })
        self.save()
        return True
    
    def update_contact(self, index: int, name: str, number: str, group: str) -> bool:
        """Update existing contact."""
        if 0 <= index < len(self.contacts):
            self.contacts[index] = {
                "name": name,
                "number": number,
                "group": group
            }
            self.save()
            return True
        return False
    
    def delete_contact(self, index: int) -> bool:
        """Delete contact by index."""
        if 0 <= index < len(self.contacts):
            del self.contacts[index]
            self.save()
            return True
        return False
    
    def get_contacts_by_group(self, group: str) -> List[Dict[str, str]]:
        """Get all contacts in a specific group."""
        return [c for c in self.contacts if c['group'] == group]
    
    def get_groups(self) -> List[str]:
        """Get all unique group names."""
        groups = set(c['group'] for c in self.contacts)
        return sorted(list(groups))
    
    def search_contacts(self, query: str) -> List[Dict[str, str]]:
        """Search contacts by name or number."""
        query = query.lower()
        return [
            c for c in self.contacts 
            if query in c['name'].lower() or query in c['number']
        ]
    
    def get_display_list(self, group_filter: Optional[str] = None) -> List[str]:
        """
        Get formatted list of contacts for display.
        
        Returns:
            List of strings like "📱 Name: +1234567890 [Group]"
        """
        contacts_to_show = self.contacts
        if group_filter and group_filter != "All":
            contacts_to_show = self.get_contacts_by_group(group_filter)
        
        return [
            f"📱 {c['name']}: {c['number']} [{c['group']}]"
            for c in contacts_to_show
        ]
    
    def import_from_csv(self, csv_path: str) -> int:
        """Import contacts from CSV file."""
        import csv
        count = 0
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'name' in row and 'number' in row:
                        group = row.get('group', 'Imported')
                        if self.add_contact(row['name'], row['number'], group):
                            count += 1
        except Exception as e:
            print(f"Error importing CSV: {e}")
        return count
    
    def export_to_csv(self, csv_path: str) -> bool:
        """Export contacts to CSV file."""
        import csv
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['name', 'number', 'group']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.contacts)
            return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False

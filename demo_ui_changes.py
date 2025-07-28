#!/usr/bin/env python3
"""
Demo script to show the UI changes made to the chat interface.
This demonstrates the changes without requiring a backend connection.
"""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class DemoMainWindow(QMainWindow):
    """Demo window to show the chat interface changes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Interface Changes Demo")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Demo buttons
        old_button = QPushButton("Show OLD format (with Assistant ID)")
        old_button.clicked.connect(self.show_old_format)
        layout.addWidget(old_button)
        
        new_button = QPushButton("Show NEW format (with Model Name)")
        new_button.clicked.connect(self.show_new_format)
        layout.addWidget(new_button)
        
        clear_button = QPushButton("Clear Chat")
        clear_button.clicked.connect(self.chat_display.clear)
        layout.addWidget(clear_button)
        
        # Show initial demo
        self.show_initial_demo()
    
    def show_initial_demo(self):
        """Show initial explanation."""
        self.chat_display.append("=== Chat Interface Changes Demo ===\n")
        self.chat_display.append("This demo shows the changes made to the chat interface:\n")
        self.chat_display.append("1. Assistant ID is replaced with model name")
        self.chat_display.append("2. Message completion notification is removed")
        self.chat_display.append("\nClick the buttons below to see the difference!\n")
    
    def show_old_format(self):
        """Show the old format with Assistant ID and completion message."""
        self.chat_display.append("\n--- OLD FORMAT ---")
        self.chat_display.append("User: Hello, how are you?")
        self.chat_display.append("\n🤖 Assistant (ID: abc12345...):")
        self.chat_display.append("I'm doing well, thank you for asking! How can I help you today?")
        self.chat_display.append("\n✅ Message completed (ID: abc12345...)")
    
    def show_new_format(self):
        """Show the new format with full model name and space after colon."""
        self.chat_display.append("\n--- NEW FORMAT ---")
        self.chat_display.append("User: Hello, how are you?")
        self.chat_display.append("\n🤖 claude-3-5-sonnet-20241022: ")
        self.chat_display.append("I'm doing well, thank you for asking! How can I help you today?")
        # Notice: No completion message here - clean end!


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    window = DemoMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

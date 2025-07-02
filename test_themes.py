#!/usr/bin/env python3
"""
Theme System Test Script

This script demonstrates the dark/light mode functionality
without requiring a backend connection.
"""

import sys
import asyncio
from PySide6.QtWidgets import QApplication
import qasync

# Import our theme system
from src.themes import get_theme_manager
from src.controllers.main_window import MainWindowController


def main():
    """Test the theme system"""
    print("🎨 Testing Chat PySide Frontend Theme System")
    print("=" * 50)

    # Create QApplication
    app = QApplication(sys.argv)

    # Set up qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Get theme manager
    theme_manager = get_theme_manager()

    print(f"📋 Initial theme: {theme_manager.current_mode.value}")
    print(f"📋 Theme info: {theme_manager.get_theme_info()}")

    # Create main window
    main_window = MainWindowController()
    main_window.show()

    print("\n🚀 Application started successfully!")
    print("💡 Click the theme toggle button to switch between light and dark modes")
    print("🔄 Theme changes are applied instantly with Material Design colors")
    print("⚡ Theme preferences are automatically saved")
    print("\n📝 Features implemented:")
    print("   ✅ Material Design 3 color system")
    print("   ✅ Real-time theme switching")
    print("   ✅ Persistent theme preferences")
    print("   ✅ Resource structure for Material Design Icons")
    print("   ✅ Performance-optimized stylesheet caching")
    print("   ✅ Signal-based theme updates")

    # Run the application
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()

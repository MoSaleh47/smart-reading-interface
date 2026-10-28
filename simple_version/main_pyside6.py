#!/usr/bin/env python3
"""
Gesture-Controlled Reading Interface
AI-HCI Project - Computer Vision Based Interaction

Authors: [Your names]
Date: January 2026
Course: AI and Human-Machine Interface (PGE5)

Description:
    A reading application controlled entirely through hand gestures.
    Uses computer vision to detect hand movements for intuitive, 
    touchless document navigation and control.

AI Techniques Used:
    - Hand gesture recognition (MediaPipe Hands)
    - Real-time landmark detection (21 points per hand)
    - Computer vision for gesture classification
    - Adaptive UI responding to user input
"""

import sys
from PySide6.QtWidgets import QApplication
from gesture_detector import GestureDetector
from reader_ui_pyside6 import ReaderUI

def main():
    print("="*60)
    print("Gesture-Controlled Reading Interface")
    print("="*60)
    print("\n🚀 Starting application...\n")

    print("📌 Gesture Controls:")
    print("   ✋ Spread fingers → Zoom IN")
    print("   🤏 Pinch fingers → Zoom OUT")
    print("   👉 Swipe Right → Next Page")
    print("   👈 Swipe Left → Previous Page")
    print()
    print("💡 Tips:")
    print("   • Hold gestures for 0.5 seconds")
    print("   • Make clear, deliberate movements")
    print("   • Keep hand visible to camera")
    print()
    print("="*60)
    print()

    # Initialize gesture detector
    print("🔧 Initializing hand gesture detection...")
    gesture_detector = GestureDetector()
    print("✅ Gesture detector ready!\n")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create and show main window
    window = ReaderUI(gesture_detector)
    window.show()

    print("✅ Application running!")
    print("💡 Use hand gestures to control the interface!\n")

    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

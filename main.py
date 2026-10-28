#!/usr/bin/env python3
"""
Smart Reading Interface with Audio Word Tracking + Gesture Control
AI-HCI Project - Multimodal Interaction System

Author: Samir Mahamat Saleh
Date: January 2026
Course: AI and Human-Machine Interface (PGE5), aivancity School of AI & Data

Description:
    An innovative reading application that combines speech recognition and hand  
    gesture control. As you read aloud, words highlight in real-time!

AI Techniques Used:
    - Real-time speech recognition (Google Speech API)
    - Hand gesture recognition (MediaPipe Hands)
    - Natural language processing for word matching
    - Computer vision for gesture detection
"""

import sys
from PySide6.QtWidgets import QApplication
from gesture_detector import GestureDetector
from audio_tracker import AudioWordTracker
from reader_ui import ReaderUI

def main():
    print("="*60)
    print("Smart Reading Interface - Audio + Gesture Control")
    print("="*60)
    print("\n🚀 Starting application...\n")

    print("📌 How to Use:")
    print("   📖 READ ALOUD - Words highlight as you speak!")
    print("   ✋ Spread fingers → Zoom IN")
    print("   🤏 Pinch fingers → Zoom OUT")
    print("   👉 Swipe Right → Next Page")
    print("   👈 Swipe Left → Previous Page")
    print()
    print("🎤 Audio Features:")
    print("   • Microphone captures your voice")
    print("   • Speech recognition identifies words")
    print("   • Words highlight in yellow as you read")
    print("   • Works in real-time!")
    print()
    print("🔒 Privacy Notice:")
    print("   Video and gesture processing run locally, and nothing is written to disk.")
    print("   Speech recognition does NOT: audio is sent to Google's speech API to be")
    print("   transcribed. Do not read anything confidential aloud.")
    print("="*60)
    print()

    # Initialize AI modules
    print("🔧 Initializing AI modules...")
    print("   🎤 Setting up microphone...")
    gesture_detector = GestureDetector()
    audio_tracker = AudioWordTracker()
    print("✅ AI modules ready!\n")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Create and show main window
    window = ReaderUI(gesture_detector, audio_tracker)
    window.show()

    print("✅ Application running!")
    print("💡 Tip: Start reading aloud and watch words highlight!\n")
    print("🎤 Speak clearly, one word at a time for best results.\n")

    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
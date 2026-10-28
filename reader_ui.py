from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                   QLabel, QPushButton, QTextEdit, QSlider, QGroupBox, 
                                   QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap, QTextCursor, QTextCharFormat, QColor
import cv2
import os

class ReaderUI(QMainWindow):
    def __init__(self, gesture_detector, audio_tracker):
        super().__init__()
        self.gesture_detector = gesture_detector
        self.audio_tracker = audio_tracker

        # Reading state
        self.current_page = 0
        self.zoom_level = 14
        self.text_content = []
        self.current_file = "Default Content"
        self.load_sample_text()

        # Word tracking
        self.current_highlighted_word = ""

        # UI Setup
        self.setWindowTitle("Smart Reading Interface - Audio + Gesture Control")
        self.setGeometry(100, 100, 1400, 800)
        self.setup_ui()

        # Camera setup
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.camera = cv2.VideoCapture(1)

        # Start audio tracking
        self.audio_tracker.start_listening()

        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ~30 FPS

    def setup_ui(self):
        """Create the main interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # LEFT PANEL
        left_panel = QVBoxLayout()

        # Camera display
        camera_group = QGroupBox("📹 Gesture Control")
        camera_layout = QVBoxLayout()
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(480, 360)
        self.camera_label.setStyleSheet("border: 2px solid #4CAF50; background: black;")
        camera_layout.addWidget(self.camera_label)
        camera_group.setLayout(camera_layout)
        left_panel.addWidget(camera_group)

        # Status indicators
        status_group = QGroupBox("📊 Real-Time Status")
        status_layout = QVBoxLayout()

        self.gesture_label = QLabel("Gesture: None")
        self.gesture_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 13px;")

        self.audio_label = QLabel("🎤 Listening...")
        self.audio_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 11px;")

        self.word_label = QLabel("Current Word: --")
        self.word_label.setStyleSheet("""
            font-weight: bold; 
            color: #FF5722; 
            font-size: 15px;
            padding: 8px;
            background-color: #FFF3E0;
            border-radius: 3px;
            border: 2px solid #FFB74D;
        """)

        status_layout.addWidget(self.gesture_label)
        status_layout.addWidget(self.audio_label)
        status_layout.addWidget(self.word_label)
        status_group.setLayout(status_layout)
        left_panel.addWidget(status_group)

        # Controls
        control_group = QGroupBox("🎮 Controls")
        control_layout = QVBoxLayout()

        # Load document
        self.load_btn = QPushButton("📁 Load Document (PDF/TXT)")
        self.load_btn.clicked.connect(self.load_document)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        control_layout.addWidget(self.load_btn)

        # Zoom controls
        zoom_label = QLabel("Font Size:")
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(32)
        self.zoom_slider.setValue(self.zoom_level)
        self.zoom_slider.valueChanged.connect(self.on_zoom_change)

        # Page controls
        page_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_page)
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.next_btn)

        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_slider)
        control_layout.addLayout(page_layout)
        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # Tips
        tips_group = QGroupBox("💡 Quick Guide")
        tips_layout = QVBoxLayout()
        tips_text = QLabel(
            "🎤 SPEECH: Say 1-2 words, pause briefly\n"
            "✋ SPREAD FINGERS: Zoom IN\n"
            "🤏 PINCH FINGERS: Zoom OUT\n"
            "👉 SWIPE HAND: Fast L/R movement"
        )
        tips_text.setStyleSheet("font-size: 10px; color: #555; line-height: 1.6;")
        tips_layout.addWidget(tips_text)
        tips_group.setLayout(tips_layout)
        left_panel.addWidget(tips_group)

        left_panel.addStretch()

        # RIGHT PANEL
        right_panel = QVBoxLayout()

        # File name
        self.file_label = QLabel("📄 " + self.current_file)
        self.file_label.setStyleSheet("font-size: 12px; color: #666; padding: 5px;")
        right_panel.addWidget(self.file_label)

        # Page indicator
        self.page_label = QLabel("Page 1 / 3")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        right_panel.addWidget(self.page_label)

        # Text display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #FEFEFE;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                padding: 30px;
                line-height: 2.2;
                color: #333;
            }
        """)
        right_panel.addWidget(self.text_display)

        # Add panels
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

        # Initial display
        self.update_text_display()

    def load_sample_text(self):
        """Load sample content"""
        self.text_content = [
            """Human Computer Interaction is the study of how people interact with computers and technology.

Modern systems use artificial intelligence to create adaptive interfaces that respond to user behavior.

Eye tracking and gesture recognition enable natural multimodal interaction.

Voice control provides hands free accessibility for users with motor disabilities.

Real time speech recognition highlights words as you read them aloud.""",

            """Speech recognition technology converts spoken words into text using machine learning algorithms.

MediaPipe provides hand tracking with twenty one landmarks per hand detected in real time.

Natural language processing enables computers to understand human communication patterns.

Accessibility features make technology usable for people with diverse abilities and needs.""",

            """Multimodal interfaces combine multiple input methods like voice gestures and touch.

Computer vision detects hand movements for touchless control of digital interfaces.

Artificial intelligence adapts to individual user preferences and behavior patterns.

Human centered design prioritizes usability accessibility and user experience."""
        ]

    def load_document(self):
        """Load PDF or TXT"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "", 
            "Documents (*.pdf *.txt);;PDF Files (*.pdf);;Text Files (*.txt)"
        )

        if file_path:
            try:
                if file_path.lower().endswith('.pdf'):
                    self.load_pdf(file_path)
                elif file_path.lower().endswith('.txt'):
                    self.load_txt(file_path)

                self.current_file = os.path.basename(file_path)
                self.file_label.setText("📄 " + self.current_file)
                self.current_page = 0
                self.update_text_display()

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load: {str(e)}")

    def load_pdf(self, file_path):
        """Load PDF"""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            self.text_content = []

            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    self.text_content.append(text)

            if not self.text_content:
                raise Exception("No text found")
        except ImportError:
            QMessageBox.warning(self, "Missing Library", "Install: pip install pypdf")
            raise

    def load_txt(self, file_path):
        """Load TXT"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        chunks = [content[i:i+1200] for i in range(0, len(content), 1200)]
        self.text_content = chunks if chunks else [content]

    def update_frame(self):
        """Update camera and process gestures/audio"""
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.flip(frame, 1)

            # Process gestures
            frame, gesture = self.gesture_detector.detect(frame)
            self.handle_gesture(gesture)

            # Display camera
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            qt_image = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
                self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio
            ))

        # Process audio
        self.handle_audio()

    def handle_gesture(self, gesture):
        """Handle gestures with VISUAL FEEDBACK"""
        from gesture_detector import Gesture

        gesture_name = gesture.name.replace('_', ' ').title()

        # Color-coded feedback
        if gesture == Gesture.ZOOM_IN:
            self.gesture_label.setText(f"✅ Gesture: {gesture_name}")
            self.gesture_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 13px;")
            self.zoom_level = min(32, self.zoom_level + 2)
            self.zoom_slider.setValue(self.zoom_level)
        elif gesture == Gesture.ZOOM_OUT:
            self.gesture_label.setText(f"✅ Gesture: {gesture_name}")
            self.gesture_label.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 13px;")
            self.zoom_level = max(10, self.zoom_level - 2)
            self.zoom_slider.setValue(self.zoom_level)
        elif gesture == Gesture.NEXT_PAGE:
            self.gesture_label.setText(f"➡️ Gesture: {gesture_name}")
            self.gesture_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 13px;")
            self.next_page()
        elif gesture == Gesture.PREV_PAGE:
            self.gesture_label.setText(f"⬅️ Gesture: {gesture_name}")
            self.gesture_label.setStyleSheet("font-weight: bold; color: #9C27B0; font-size: 13px;")
            self.prev_page()
        else:
            self.gesture_label.setText(f"Gesture: {gesture_name}")
            self.gesture_label.setStyleSheet("font-weight: bold; color: #757575; font-size: 13px;")

    def handle_audio(self):
        """Handle audio word tracking with VISUAL FEEDBACK"""
        current_word = self.audio_tracker.get_current_word()
        last_text = self.audio_tracker.get_last_text()

        if last_text:
            # Truncate if too long
            display_text = last_text if len(last_text) < 50 else last_text[:47] + "..."
            self.audio_label.setText(f"🎤 Heard: '{display_text}'")
            self.audio_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 11px;")

        if current_word and current_word != self.current_highlighted_word:
            self.current_highlighted_word = current_word
            self.word_label.setText(f"📍 Current: {current_word.upper()}")
            self.highlight_word(current_word)

    def highlight_word(self, word):
        """Highlight word in text"""
        if not word:
            return

        cursor = self.text_display.textCursor()
        doc = self.text_display.document()

        # Clear previous highlights
        cursor.select(QTextCursor.SelectionType.Document)
        format_clear = QTextCharFormat()
        format_clear.setBackground(QColor(255, 255, 255))
        cursor.mergeCharFormat(format_clear)
        cursor.clearSelection()

        # Highlight current word (case-insensitive)
        text = doc.toPlainText().lower()
        word_lower = word.lower()

        # Find all occurrences
        start = 0
        highlighted_count = 0
        while True:
            pos = text.find(word_lower, start)
            if pos == -1:
                break

            # Check if it's a whole word
            is_word_boundary = True
            if pos > 0 and text[pos-1].isalnum():
                is_word_boundary = False
            if pos + len(word_lower) < len(text) and text[pos + len(word_lower)].isalnum():
                is_word_boundary = False

            if is_word_boundary:
                cursor.setPosition(pos)
                cursor.setPosition(pos + len(word_lower), QTextCursor.MoveMode.KeepAnchor)

                # Highlight format
                format_highlight = QTextCharFormat()
                format_highlight.setBackground(QColor(255, 235, 59))  # Yellow
                format_highlight.setForeground(QColor(0, 0, 0))
                format_highlight.setFontWeight(QFont.Weight.Bold)
                cursor.mergeCharFormat(format_highlight)
                highlighted_count += 1

            start = pos + 1

    def on_zoom_change(self, value):
        """Update zoom"""
        self.zoom_level = value
        self.update_text_display()

    def next_page(self):
        """Next page"""
        if self.current_page < len(self.text_content) - 1:
            self.current_page += 1
            self.update_text_display()

    def prev_page(self):
        """Previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_text_display()

    def update_text_display(self):
        """Update text"""
        if not self.text_content:
            return

        font = QFont("Arial", self.zoom_level)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 105)
        self.text_display.setFont(font)
        self.text_display.setPlainText(self.text_content[self.current_page])
        self.page_label.setText(f"Page {self.current_page + 1} / {len(self.text_content)}")

        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < len(self.text_content) - 1)

    def closeEvent(self, event):
        """Cleanup"""
        self.timer.stop()
        self.camera.release()
        self.gesture_detector.release()
        self.audio_tracker.release()
        event.accept()
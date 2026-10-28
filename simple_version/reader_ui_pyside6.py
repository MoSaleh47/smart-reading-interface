from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                   QLabel, QPushButton, QTextEdit, QSlider, QGroupBox, 
                                   QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
import cv2
import os

class ReaderUI(QMainWindow):
    def __init__(self, gesture_detector):
        super().__init__()
        self.gesture_detector = gesture_detector

        # Reading state
        self.current_page = 0
        self.zoom_level = 14
        self.text_content = []
        self.current_file = "Default Content"
        self.load_sample_text()

        # UI Setup
        self.setWindowTitle("Gesture-Controlled Reading Interface - AI-HCI Project")
        self.setGeometry(100, 100, 1400, 800)
        self.setup_ui()

        # Camera setup
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            self.camera = cv2.VideoCapture(1)

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
        camera_group = QGroupBox("📹 Hand Gesture Detection")
        camera_layout = QVBoxLayout()
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(480, 360)
        self.camera_label.setStyleSheet("border: 2px solid #4CAF50; background: black;")
        camera_layout.addWidget(self.camera_label)
        camera_group.setLayout(camera_layout)
        left_panel.addWidget(camera_group)

        # Status indicators
        status_group = QGroupBox("📊 Status")
        status_layout = QVBoxLayout()

        self.gesture_label = QLabel("Gesture: None")
        self.gesture_label.setStyleSheet("""
            font-weight: bold; 
            color: #2196F3; 
            font-size: 14px;
            padding: 5px;
        """)

        status_layout.addWidget(self.gesture_label)
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
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        control_layout.addWidget(self.load_btn)

        # Zoom controls
        zoom_label = QLabel("Font Size:")
        zoom_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(32)
        self.zoom_slider.setValue(self.zoom_level)
        self.zoom_slider.valueChanged.connect(self.on_zoom_change)

        self.zoom_value_label = QLabel(f"{self.zoom_level}pt")
        self.zoom_value_label.setStyleSheet("color: #666; font-size: 11px;")

        # Page controls
        page_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                font-weight: bold;
            }
        """)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                font-weight: bold;
            }
        """)
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.next_btn)

        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_slider)
        control_layout.addWidget(self.zoom_value_label)
        control_layout.addLayout(page_layout)
        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # Gesture guide
        tips_group = QGroupBox("💡 Gesture Controls")
        tips_layout = QVBoxLayout()
        tips_text = QLabel(
            "✋ <b>SPREAD FINGERS</b><br>"
            "   → Zoom IN<br><br>"
            "🤏 <b>PINCH FINGERS</b><br>"
            "   → Zoom OUT<br><br>"
            "👉 <b>SWIPE RIGHT</b><br>"
            "   → Next Page<br><br>"
            "👈 <b>SWIPE LEFT</b><br>"
            "   → Previous Page"
        )
        tips_text.setWordWrap(True)
        tips_text.setStyleSheet("font-size: 11px; color: #555; line-height: 1.8;")
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
        self.page_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        right_panel.addWidget(self.page_label)

        # Text display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #FEFEFE;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                padding: 35px;
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
            """Human Computer Interaction

Human-Computer Interaction (HCI) is the study of how people interact with computers and to what extent computers are developed for successful interaction with human beings.

As technology continues to evolve, the importance of intuitive and accessible interfaces becomes increasingly critical.

Modern HCI incorporates artificial intelligence to create adaptive systems that respond to user behavior, emotions, and preferences.

This paradigm shift enables more natural and efficient human-machine communication through multimodal interaction.""",

            """Gesture Recognition Technology

Gesture recognition interprets human movements via mathematical algorithms and computer vision techniques.

Hand gestures provide an intuitive method for human-computer interaction, especially in scenarios where touch input is impractical or impossible.

MediaPipe and similar frameworks enable real-time hand tracking using advanced computer vision models that detect 21 hand landmarks.

These systems classify predefined gestures, allowing touchless control of digital interfaces for applications in healthcare, automotive, gaming, and accessibility technology.""",

            """Computer Vision Applications

Computer vision enables machines to derive meaningful information from visual inputs such as images and videos.

Applications span facial recognition, object detection, autonomous vehicles, medical imaging, and augmented reality.

Deep learning models, particularly convolutional neural networks, have revolutionized computer vision by achieving human-level accuracy in many tasks.

Real-time processing allows for immediate feedback and interaction, making computer vision essential for modern human-computer interfaces."""
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
                raise Exception("No text found in PDF")
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
        """Update camera and process gestures"""
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

    def handle_gesture(self, gesture):
        """Handle gestures with visual feedback"""
        from gesture_detector import Gesture

        gesture_name = gesture.name.replace('_', ' ').title()

        # Color-coded feedback
        if gesture == Gesture.ZOOM_IN:
            self.gesture_label.setText(f"✅ {gesture_name}")
            self.gesture_label.setStyleSheet("""
                font-weight: bold; 
                color: #4CAF50; 
                font-size: 14px;
                padding: 5px;
                background-color: #E8F5E9;
                border-radius: 3px;
            """)
            self.zoom_level = min(32, self.zoom_level + 2)
            self.zoom_slider.setValue(self.zoom_level)
        elif gesture == Gesture.ZOOM_OUT:
            self.gesture_label.setText(f"✅ {gesture_name}")
            self.gesture_label.setStyleSheet("""
                font-weight: bold; 
                color: #FF9800; 
                font-size: 14px;
                padding: 5px;
                background-color: #FFF3E0;
                border-radius: 3px;
            """)
            self.zoom_level = max(10, self.zoom_level - 2)
            self.zoom_slider.setValue(self.zoom_level)
        elif gesture == Gesture.NEXT_PAGE:
            self.gesture_label.setText(f"➡️ {gesture_name}")
            self.gesture_label.setStyleSheet("""
                font-weight: bold; 
                color: #2196F3; 
                font-size: 14px;
                padding: 5px;
                background-color: #E3F2FD;
                border-radius: 3px;
            """)
            self.next_page()
        elif gesture == Gesture.PREV_PAGE:
            self.gesture_label.setText(f"⬅️ {gesture_name}")
            self.gesture_label.setStyleSheet("""
                font-weight: bold; 
                color: #9C27B0; 
                font-size: 14px;
                padding: 5px;
                background-color: #F3E5F5;
                border-radius: 3px;
            """)
            self.prev_page()
        else:
            self.gesture_label.setText(f"Gesture: {gesture_name}")
            self.gesture_label.setStyleSheet("""
                font-weight: bold; 
                color: #757575; 
                font-size: 14px;
                padding: 5px;
            """)

    def on_zoom_change(self, value):
        """Update zoom"""
        self.zoom_level = value
        self.zoom_value_label.setText(f"{value}pt")
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
        event.accept()

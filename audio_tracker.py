import speech_recognition as sr
import threading
import queue
import time

class AudioWordTracker:
    """Real-time speech recognition with MINIMAL DELAY"""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Audio processing
        self.is_listening = False
        self.current_word = ""
        self.last_recognized_text = ""

        # Adjust for ambient noise (faster)
        print("🎤 Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)  # Reduced from 1s
        print("✅ Microphone ready!")

        # Recognition settings for LOW LATENCY
        self.recognizer.energy_threshold = 250  # Lower = more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.3  # VERY SHORT pauses (was 0.5)
        self.recognizer.phrase_threshold = 0.1  # Minimum audio before phrase
        self.recognizer.non_speaking_duration = 0.3  # Quick silence detection

    def start_listening(self):
        """Start background listening"""
        if not self.is_listening:
            self.is_listening = True
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()

    def stop_listening(self):
        """Stop background listening"""
        self.is_listening = False

    def _listen_loop(self):
        """Background thread for continuous listening - OPTIMIZED FOR SPEED"""
        with self.microphone as source:
            while self.is_listening:
                try:
                    # Listen with SHORT timeout and phrase limit
                    audio = self.recognizer.listen(
                        source, 
                        timeout=0.5,  # Very short timeout
                        phrase_time_limit=2  # Max 2 seconds per phrase (was 3)
                    )

                    # Recognize in background (non-blocking)
                    threading.Thread(
                        target=self._recognize_audio, 
                        args=(audio,), 
                        daemon=True
                    ).start()

                except sr.WaitTimeoutError:
                    # Timeout is expected, continue listening
                    continue
                except Exception as e:
                    # Don't spam errors
                    time.sleep(0.1)

    def _recognize_audio(self, audio):
        """Recognize audio FAST"""
        try:
            # Use Google Speech Recognition
            # Set language to English for faster processing
            text = self.recognizer.recognize_google(
                audio, 
                language='en-US',
                show_all=False  # Only get top result (faster)
            )

            if text:
                self.last_recognized_text = text
                # Get last word spoken
                words = text.split()
                if words:
                    # Get last 1-2 words (more responsive)
                    if len(words) >= 2:
                        self.current_word = words[-1].lower().strip('.,!?;:"')
                    else:
                        self.current_word = words[-1].lower().strip('.,!?;:"')

        except sr.UnknownValueError:
            # Speech not understood - ignore silently
            pass
        except sr.RequestError:
            # API error - ignore to avoid spam
            pass
        except Exception:
            pass

    def get_current_word(self):
        """Get the most recently recognized word"""
        return self.current_word

    def get_last_text(self):
        """Get the last full recognized text"""
        return self.last_recognized_text

    def clear_word(self):
        """Clear current word"""
        self.current_word = ""

    def release(self):
        """Clean up resources"""
        self.stop_listening()
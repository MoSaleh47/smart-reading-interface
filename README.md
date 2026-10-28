# Smart Reading Interface

A hands-free reading application driven by **speech** and **hand gestures**. You read a
document out loud and the words highlight as you say them; you turn pages and change the font
size with gestures in front of the webcam, without touching the keyboard.

Built for the AI and Human-Machine Interface course at aivancity School of AI & Data
(Programme Grande École), 2026.

---

## What it does

**Speech word tracking.** A background thread listens on the microphone, transcribes short
utterances and matches them against the words of the open document. Matched words highlight as
you read, so the page follows your voice.

**Gesture control.** MediaPipe Hands tracks 21 hand landmarks per frame; a classifier on top of
those landmarks maps hand shapes to commands, with a cooldown so one gesture does not fire
repeatedly.

| Gesture | Action |
|---|---|
| Spread fingers | Zoom in |
| Pinch (thumb + index) | Zoom out |
| Swipe right | Next page |
| Swipe left | Previous page |

**Reader UI.** A PySide6 desktop window showing the document, the live camera feed with the
detected landmarks drawn on it, and the current gesture and recognition state.

---

## Privacy: speech is sent to Google

`audio_tracker.py` uses `SpeechRecognition`'s `recognize_google()`, so **captured audio is sent
to Google's speech API for transcription**. It is not processed on your machine.

Nothing is written to disk by this application, and the video stream never leaves it — gesture
and gaze processing are genuinely local. The audio is not, and you should assume anything read
aloud reaches a third party.

To make the whole pipeline local, swap `recognize_google()` for an offline recogniser such as
Vosk or `faster-whisper`. That is the first change worth making to this project.

---

## Install and run

Requires Python 3.8+, a webcam and a microphone.

```bash
pip install -r requirements.txt
python main.py
```

`PyAudio` is needed for microphone capture and has no wheel on some platforms. On Windows,
`pip install pipwin && pipwin install pyaudio` usually resolves it; on Debian/Ubuntu install
`portaudio19-dev` first.

---

## Layout

```
main.py                 entry point: wires the detectors into the UI
reader_ui.py            PySide6 window, document rendering, camera panel
gesture_detector.py     MediaPipe Hands -> Gesture enum, with cooldown
audio_tracker.py        microphone capture, transcription, word matching
gaze_tracker.py         MediaPipe Face Mesh iris tracking + fixation detection
simple_version/         reduced build: gestures only, no audio
```

### A note on `gaze_tracker.py`

This module implements iris tracking and fixation detection with MediaPipe Face Mesh, and works
standalone — but **it is not wired into `main.py`**. The application as it ships runs on speech
and gestures. The gaze module is from an earlier iteration, kept because the fixation logic is
the most interesting part of the project and is worth reading.

Integrating it — estimating which line the reader is on, and auto-scrolling — is the natural
next step.

---

## How the gesture classifier works

MediaPipe returns normalised landmark coordinates per hand. Rather than train a model,
`gesture_detector.py` classifies geometrically:

- **Pinch and spread** come from the distance between thumb tip and index tip, normalised by
  hand size so the result does not change as the hand moves nearer to or further from the
  camera.
- **Swipes** come from the displacement of the hand centroid between frames, with a minimum
  velocity so slow drift is not read as a swipe.
- A cooldown suppresses repeat firing while a gesture is held.

This is deliberate: the rules are inspectable and need no training data, which matters when the
alternative is a black box controlling someone's reading interface.

---

## Limitations

- Speech recognition needs a network connection and a quiet room. It degrades with accents and
  with fast continuous reading, since it matches word by word.
- Gesture detection needs reasonable lighting, with the hand 30–60 cm from the camera.
- The gaze module assumes a roughly frontal face and is not calibrated per user, so its
  screen-position estimate is indicative rather than accurate.
- Timings observed during development (~30 FPS, sub-100 ms gesture response on an Intel i5)
  were noted informally, not benchmarked.

---

## Ethics

The application handles two kinds of biometric signal: hand geometry and, in the gaze module,
iris position. Neither is stored and neither leaves the machine. Audio does leave the machine,
as described above.

Camera and microphone dependence is itself an accessibility limit: the gestures assume a user
who can make them, which is a real constraint on an interface whose purpose is accessibility.
Manual controls remain available for every action.

---

## Author

Samir Mahamat Saleh — [github.com/MoSaleh47](https://github.com/MoSaleh47)

## Licence

MIT — see [LICENSE](LICENSE).

# Textbook: `scripts/inference_dashboard.py`

## 📦 Library Reference

### External Libraries
- **`tensorflow` (as `tf`)**: The "Brain" of the dashboard.
    - **Usage**: Loads the trained model (`tf.keras.models.load_model`) and performs the `model.predict()` math during live monitoring.
- **`numpy` (as `np`)**: Used for numerical processing, specifically the `np.argmax` function which decides which activity has the highest probability.
- **`datetime`**: Logs the exact second an activity was detected.
- **`argparse`**: Allows the user to select the hardware port at startup.

### Local Dependencies
- **[src.utils.serial_utils](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md)**: Used to connect to the physical ESP32.
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: Extracts subcarrier amplitudes from the serial stream.
- **[src.data.preprocessor](file:///d:/Projects/major/notes/fall_detector_logic/src/data/preprocessor.md)**: The "Signal Polisher."
    - **Usage**: Applies the exact same scaling (Standardization) to the live data that was used during the training phase.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Manages UI colors and alert sensitivity thresholds.

## 📖 Overview
The `inference_dashboard.py` is the most sophisticated script in the project. It transforms raw Wi-Fi signals into human-readable activity predictions in real-time. It features:
1.  **Terminal Dashboard**: A sleek, ANSI-colored UI that updates 12---
2.  **ML Integration**: Real-time inference using the CNN-GRU model.
3.  **EMA Smoothing**: Exponential Moving Averages to make class probability bars look "smooth" instead of jumpy.
4.  **Alerting System**: Specialized logic for detecting "Falls" and logging them to a persistent history.

## 🎓 Concept Deep-Dives

### 1. What is EMA Smoothing?
Raw AI predictions are often "jittery." One millisecond it might guess "Walk," and the next "Stand," then back to "Walk."
- **EMA (Exponential Moving Average)**: Acts like a "Debouncer." It says, "Don't just believe the latest prediction; give 60% importance to the past and only 40% to the new data."
- **The Benefit**: This creates the smooth, stable progress bars you see in the dashboard, preventing the system from flashing alerts for every tiny data glitch.

### 2. The Multi-Step Fall Logic
We don't sound the alarm for a single "Fall" prediction. Why?
- **The Challenge**: A person sitting down fast can look like a fall for a split second.
- **The Solution (Line 300)**: We use two layers of protection:
    1. **Probability Threshold (>0.65)**: The model must be very confident.
    2. **Consecutive Count (3+)**: The model must see the "Fall" pattern for 3 overlapping windows in a row. This ensures it's a real, sustained motion before notifying a caregiver.

## 🔗 Related Notes & Dependencies
- **Data Source**: This script reads live data via the [serial_utils.md](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md).
- **Processing**: Every live window is cleaned using the [preprocessor.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/preprocessor.md).
- **The Brain**: Real-time math is performed by the model defined in [cnn_gru.md](file:///d:/Projects/major/notes/fall_detector_logic/src/models/cnn_gru.md).
- **Configuration**: The thresholds and alert intervals are managed in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

---

## 💻 Code Walkthrough

### 1. Dashboard State and Locking
```python
25:     def __init__(self, port, model_path):
30:         self.lock = threading.Lock()
33:         self.inf_buffer = CSIRingBuffer(window_size=50, subcarriers=114)
43:         self.model = tf.keras.models.load_model(model_path, compile=False)
```
-   **Line 30**: Since we have three threads (Serial intake, ML inference, and UI rendering), a `Lock` is required to ensure they don't modify the `latest_prediction` or `latest_probs` simultaneously, which would cause "race conditions."
-   **Line 33**: The `inf_buffer` is the source of truth for the ML model. It stores the last 50 CSI packets.
-   **Line 43**: Loads the pre-trained `.keras` file containing the weights and layers.

### 2. The Inference Loop (The "Brain")
```python
93:     def inference_loop(self):
96:             alpha = 0.4 # EMA Smoothing
98:                 if self.inf_buffer.has_window():
99:                     raw_window = self.inf_buffer.get_recent_window()
100:                     processed = self.preprocess_window(raw_window)
103:                     probs = self.model.predict(processed, verbose=0)[0]
107:                     with self.lock:
110:                         self.smoothed_probs = (alpha * probs) + ((1 - alpha) * self.smoothed_probs)
111:                         self.latest_prediction = self.classes[np.argmax(probs)]
```
-   **Line 98-100**: Once the buffer fills with 50 packets, it extracts that "window" and applies the same preprocessing (outlier removal + global scaling) as used in training.
-   **Line 103**: Calls the Keras `predict` function. This is computationally expensive, so it runs on its own background thread.
-   **Line 110**: **EMA Smoothing**. If the model jumps from 10% to 90% "Walk", the visual bar will slide smoothly over 2-3 frames, making the dashboard easier for humans to read.

### 3. Fall Alert Logic (Safety First)
```python
141:     def _handle_alerts(self, probs):
148:         fall_prob = probs[fall_idx]
149:         if fall_prob > settings.FALL_PROBABILITY_THRESHOLD:
150:             self.consecutive_falls += 1
151:             if self.consecutive_falls >= settings.CONSECUTIVE_DETECTIONS:
154:                     self.alert_message = f"FALL DETECTED! Prob: {fall_prob:.1%}"
```
-   **Line 149-158**: **Debouncing**. To prevent a single noisy packet from triggering a "Fall" alarm, the system requires the probability to be above a threshold (e.g., 65%) for **3 consecutive detections** (approx. 750ms of data).

### 4. Optimized Terminal Rendering
```python
194:     def render_dashboard(self):
197:         CLR_RESET = "\033[0m"
203:         ANSI_HOME = "\033[H" # Move cursor to top-left
206:         os.system('cls' if os.name == 'nt' else 'clear')
224:             out.append("="*70)
252:                 out.append(f" {cls:<10} | {color}{bar}{CLR_RESET} | {prob:>6.1%}")
258:             sys.stdout.write("\n".join(out) + "\n")
```
-   **Line 203**: Instead of "clearing" the screen every time (which causes flickering), the script uses `\033[H` to teleport the cursor back to the start.
-   **Line 224-252**: Builds the entire dashboard as a list of strings in memory.
-   **Line 258**: Flushes the *entire* dashboard to the terminal in a single `write()` call. This ensures the visual output is static and professional-looking.

---

## 🎯 Key Takeaways
-   **Concurrency**: Separate threads for **I/O** (Serial), **Compute** (Inference), and **View** (Terminal) is the standard pattern for high-performance Python applications.
-   **Alignment**: Inference MUST use the same preprocessing (scaling) as training. If you fit a scaler on amplitudes that vary from 0-1000, and you try to predict on raw amplitudes, the model will output garbage results.
-   **Hysteresis**: The use of `CONSECUTIVE_DETECTIONS` adds temporal hysteresis to the classification, making the system much more robust to transient noise.

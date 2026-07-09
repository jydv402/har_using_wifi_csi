# Textbook: `src/data/parser.py`
## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: The backbone of the parser. Used extensively for high-performance array operations.
    - **Usage**: Creating the circular buffer (`np.zeros`), calculating amplitudes (`np.sqrt`, `np.square`), and stacking windowed data (`np.vstack`).
- **`scipy.interpolate` (`interp1d`)**: Used on-demand for data harmonization.
    - **Usage**: Resizes CSI arrays (e.g., from 52 subcarriers to 114) so that data from older hardware remains compatible with modern models.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides critical hardware-specific constants.
    - **Usage**: References `settings.SUBCARRIERS` to ensure the parser knows how many frequency bands to expect.

## 📖 Overview
The `src/data/parser.py` is the translation layer of the project. It takes messy, text-based serial strings from the ESP32 and converts them into clean, mathematical matrices that an AI can understand.
1.  **`CSIParser`**: Converts raw text strings from the ESP32 (serial) into structured mathematical arrays.
2.  **`CSIRingBuffer`**: Manages a rotating window of data in memory, allowing for smooth, overlapping predictions during real-time inference.

---

## 💻 Code Walkthrough: `CSIParser`

### 1. Subcarrier Indexing
```python
14:         self.ht40_valid_indices = list(range(6, 63)) + list(range(65, 122))
18:         self.ht20_valid_indices = list(range(6, 32)) + list(range(33, 59))
```
-   **Lines 14-18**: Wi-Fi signals include "Pilot" carriers and "Guard" carriers which don't contain data or are too noisy to use. These lists define the "Good" subcarrier indices for both 20MHz (52 carriers) and 40MHz (114 carriers) modes.

### 2. Signal Harmonization (Interpolation)
```python
28:         from scipy.interpolate import interp1d
31:         f = interp1d(x, csi, kind='linear')
32:         return f(x_new).astype(np.float32)
```
-   **Lines 28-32**: If we collect data from an old 20MHz router (52 carriers) but our model was trained on 40MHz (114 carriers), we use linear interpolation to "stretch" the 52 values into 114. This ensures our models are backward-compatible with different hardware.

### 3. From IQ to Amplitude
```python
63:             iq_values = np.fromstring(payload_str, sep=",", dtype=np.int16)
67:             i_vals = iq_values[0::2].astype(np.float32)
68:             q_vals = iq_values[1::2].astype(np.float32)
69:             amplitudes = np.sqrt(i_vals**2 + q_vals**2)
```
-   **Line 63**: The raw string `[10, -5, 12, 3...]` contains interleaved I (In-phase) and Q (Quadrature) components.
-   **Lines 67-68**: Separates the I and Q values using Python slicing (`[0::2]` means start at 0 and take every second item).
-   **Line 69**: Calculates the **Euclidean Norm** (Amplitude). This is the standard "Signal Strength" for each subcarrier.

---

## 💻 Code Walkthrough: `CSIRingBuffer`

### 1. Circular Buffer Implementation
```python
114:         self.buffer = np.zeros((window_size * 2, subcarriers), dtype=np.float32)
129:         self.head = (self.head + 1) % (self.window_size * 2)
```
-   **Line 114**: We create a buffer twice the size of our target window. This provides a "safety margin" so we can extract windows without worrying about the internal pointer overlapping itself during a single read.
-   **Line 129**: The `%` (Modulo) operator keeps the `head` pointer looping back to 0 once it reaches the end, creating a "Circle".

### 2. Window Extraction
```python
142:         start_idx = (self.head - self.window_size) % (self.window_size * 2)
144:         if start_idx < self.head:
146:             return self.buffer[start_idx:self.head].copy()
148:         else:
149:             return np.vstack((self.buffer[start_idx:], self.buffer[:self.head]))
```
-   **Line 142**: Calculates where the current "Oldest" data in our window is.
-   **Line 144-149**: Handles the **Wraparound Case**. If the window spans across the end and start of the buffer, it "glues" the two pieces together using `np.vstack`.

---

---

## 🎓 Concept Deep-Dives

### 1. From I/Q to Amplitude (The Math)
Wi-Fi signals are complex numbers. They have an **I (In-phase)** part and a **Q (Quadrature)** part.
- **Analogy**: I and Q are like the North-South and East-West coordinates on a map.
- **The Goal**: We want to know the total "Distance" from the start—this is the **Amplitude**.
- **The Formula (Line 69)**: `sqrt(I² + Q²)`. This converts the electrical vibrations into a simple "Signal Strength" that the machine learning model can understand.

### 2. Why use Interpolation? (52 -> 114 subcarriers)
As explained on Line 28, we use `scipy.interpolate` to resize our data.
- **The Reason**: Older Wi-Fi chips only report 52 data points. Our project standards (HT40) use 114 points.
- **The Fix**: Interpolation "draws a smooth line" through the 52 points and maps out 114 points on that line. This makes the project **Hardware Compatible**—you can use data from almost any ESP32 device!

---

## 🔗 Related Notes & Dependencies
- **Consumer**: The parsed amplitudes are sent to the [preprocessor.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/preprocessor.md) for cleaning.
- **Hardware Source**: The raw strings parsed here originate from the [rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md).
- **Configuration**: The subcarrier indices are managed in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

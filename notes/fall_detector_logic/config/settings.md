# Textbook: `config/settings.py`

## 📦 Library Reference

### External Libraries
- **`pathlib` (`Path`)**: The modern file system manager.
    - **Usage**: Automatically calculates the `_ROOT` of your project so that the system works whether you are on Windows or Linux, and whether you run it from the root or a subfolder.

### Local Dependencies
- **(None)**: This is the root configuration file for the entire project.

## 📖 Overview
The `config/settings.py` is the "Control Room" of the project. Every important number—from the Wi-Fi frequency to the AI sensitivity—is defined here. By changing a single line in this file, you can retrain the whole brain for a new environment. This makes the project "Portable"—meaning you can change the hardware setup or model parameters across the whole project just by editing this one file.

---

## 💻 Code Walkthrough

### 1. Portable Path Resolution
```python
10: _ROOT = Path(__file__).parent.parent
64: DATA_DIR           = _ROOT / "data"
67: MODEL_DIR          = _ROOT / "models"
```
-   **Line 10**: Uses `Path(__file__)` to find exactly where this file is on the computer. It then goes Up two levels (`parent.parent`) to find the project root.
-   **Lines 64-67**: All other paths are built relative to `_ROOT`. This ensures the code works on Windows, Linux, or macOS without changing backslashes (`\`) to forward slashes (`/`).

### 2. Physical Constants (Wi-Fi 101)
```python
17: CSI_PACKET_RATE = 100
23: SUBCARRIERS    = 114
24: RSSI_FLOOR     = -85
```
-   **Line 17**: This heartbeat of the system. If you change the code on the ESP32 to send faster or slower, you *must* update this value here so the "Timestamping" logic stays accurate.
-   **Line 23**: Defines the **Frequency Resolution**. 114 subcarriers is standard for HT40 bandwidth.
-   **Line 24**: **The Noise Floor**. If a signal is weaker than -85dBm, it is usually just static noise. The system ignores these packets to prevent them from confusing the ML model.

### 3. ML Hyperparameters
```python
32: WINDOW_SIZE    = 50
33: HOP_SIZE       = 25
38: CNN_FILTERS    = [64, 128, 128]
42: DROPOUT_RATE   = 0.3
```
-   **Line 32**: A window size of 50 packets at 100Hz means the model looks at **0.5 seconds** of history to make a decision.
-   **Line 33**: A hop of 25 results in a **50% overlap**. This means the system outputs a new decision every 0.25 seconds.
-   **Line 42**: Dropout is set to 30%. This is a "Defense" setting that makes the model less fragile and more reliable in different rooms.

### 4. Safety and Alerts
```python
59: FALL_PROBABILITY_THRESHOLD = 0.65
60: CONSECUTIVE_DETECTIONS     = 3
```
-   **Line 59-60**: These are the "Dial" settings for the Fall Alert. 
    -   Increase `0.65` to `0.80` if you get too many false alarms.
    -   Increase `CONSECUTIVE_DETECTIONS` to `5` if the system is "jumpy" when people are just sitting down roughly.

---

---

## 🎓 Concept Deep-Dives

### 1. What is HT40?
Most Wi-Fi operates in "HT20" (20MHz). By choosing **HT40** (Line 21), we double the bandwidth.
- **Why?**: In the 2.4GHz spectrum, HT20 provides 52 subcarriers, but HT40 provides **114**. Higher subcarrier count is like having a television with more pixels—it gives the machine learning model a "High Definition" view of the room.

### 2. Choosing Window and Hop Sizes
How do we decide on `WINDOW_SIZE = 50`?
- **Sampling Rate**: We collect data at 100Hz (100 packets per second). 
- **The Memory**: A window of 50 packets equals **0.5 seconds**. 
- **The Justification**: Most human motions (like a fall or a step) take between 0.3 and 1.0 seconds. 50 is the "Sweet Spot" that captures enough of the action without including too much background noise.

---

## 🔗 Related Notes & Dependencies
- **Data Intake**: These constants are used by the [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md) to define subcarrier indices.
- **Model Construction**: The `CNN_FILTERS` (Line 38) defined here are used to build the network in [cnn_gru.md](file:///d:/Projects/major/notes/fall_detector_logic/src/models/cnn_gru.md).
- **Firmware Match**: The `BAUD_RATE` (Line 14) MUST match the setting in [rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md).

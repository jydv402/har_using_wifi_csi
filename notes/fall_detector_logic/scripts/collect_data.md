# Textbook: `scripts/collect_data.py`
## 📦 Library Reference

### External Libraries
- **`matplotlib` (`plt`, `animation`)**: The visual engine of the script.
    - **Usage**: Used to create the real-time scrolling graph. `animation.FuncAnimation` is the specific tool that allows the graph to update smoothly 20 times per second.
- **`numpy` (as `np`)**: Used for managing the signal amplitude arrays before they are saved.
- **`pandas` (as `pd`)**: The data storage specialist.
    - **Usage**: Converts the collected signal arrays into a structured CSV file with column headers.
- **`argparse`**: Handles "Command Line" instructions.
    - **Usage**: Allows you to specify the `--port` and `--activity` labels when you start the script.
- **`threading`**: Prevents the UI from freezing.

### Local Dependencies
- **[src.utils.serial_utils](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md)**: The data pipe.
    - **Usage**: Pulls the `AsyncSerialReader` to listen to the ESP32.
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: The translator.
    - **Usage**: Uses `CSIParser` and `CSIRingBuffer` to turn raw text into clean math.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: The project rulebook.

## 📖 Overview
The `scripts/collect_data.py` is the primary tool for building your own HAR dataset. It provides a visual interface to see the CSI signal live and a one-touch recording system (the Spacebar) to save clean labels of "Falling," "Walking," or "Sitting."
 It uses a **multithreaded architecture** to ensure that data is captured without interruption while the UI is being updated.

---

## 💻 Code Walkthrough

### 1. Initialization and Setup
```python
17: class DataCollector:
18:     def __init__(self, port, activity):
19:         self.port = port
20:         self.activity = activity
21:         self.reader = AsyncSerialReader(port, settings.BAUD_RATE)
22:         self.parser = CSIParser()
24:         self.vis_buffer = CSIRingBuffer(window_size=100, subcarriers=settings.SUBCARRIERS)
28:         self.target_packets = settings.CSI_PACKET_RATE * settings.SAMPLE_DURATION
```
-   **Line 21**: Initializes the `AsyncSerialReader`. This runs in its own thread to "drain" the serial buffer from the ESP32 as fast as possible.
-   **Line 24**: A `CSIRingBuffer` is used to store the last 100 packets specifically for the live plot. This ensures the plot always shows a "rolling" window of data.
-   **Line 28**: Calculates how many packets are needed for a full sample (e.g., 100Hz * 10 seconds = 1000 packets).

### 2. Threading and Animation
```python
49:     def start(self):
50:         self.reader.start()
52:         self.process_thread = threading.Thread(target=self.process_loop, daemon=True)
53:         self.process_thread.start()
57:         ani = animation.FuncAnimation(self.fig, self.update_plot, interval=30, blit=False)
```
-   **Line 52-53**: Starts the `process_loop` in a background thread. This thread is responsible for taking raw strings from the serial reader, parsing them into amplitudes, and adding them to the buffer.
-   **Line 57**: Starts the Matplotlib animation. It calls `update_plot` every 30 milliseconds to refresh the screen.

### 3. The Processing Loop
```python
66:     def process_loop(self):
67:         while self.reader.is_running:
68:             lines = self.reader.get_lines(max_lines=100)
69:             for line in lines:
70:                 parsed = self.parser.parse_line(line)
71:                 if parsed:
72:                     amp = parsed["amplitudes"]
73:                     self.vis_buffer.append(amp)
75:                     if self.saving:
76:                         self.current_sample_data.append(amp)
77:                         if len(self.current_sample_data) >= self.target_packets:
78:                             self.save_sample()
```
-   **Line 68**: Retrieves the latest lines from the serial queue.
-   **Line 70**: The `CSIParser` converts the raw string into a dictionary containing the RSSI and an array of amplitudes.
-   **Line 75-78**: If the user has triggered a recording (by pressing SPACE), the script starts accumulating the amplitudes into `current_sample_data`. Once the target count is reached, it automatically triggers `save_sample()`.

## 🎓 Concept Deep-Dives

### 1. The Importance of "Clean" Labeling
Machine learning is "Garbage In, Garbage Out." If you accidentally record a "Fall" while you were actually just "Sitting," the model will be confused forever.
- **Goal (Line 80)**: This script uses a simple UI to ensure the human operator is ready. By pressing **SPACE**, you start a laser-focused 10-second recording of one specific activity.
- **The Result**: High-quality training data where every single CSV file contains 100% of the activity it claims to have.

### 2. Threaded Visualization
Why doesn't the graph freeze when saving files?
- **Threading (Line 54)**: The script splits your computer's attention. One part of the brain listens to the Wi-Fi (`Serial Thread`), while another draws the graph (`GUI Thread`). This ensures the live data line stays "smooth" even while the computer is busy writing to the hard drive.

---

## 🔗 Related Notes & Dependencies
- **Data Intake**: Relies on the [serial_utils.md](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md) to catch the packet stream.
- **Parsing**: Every packet is processed by the [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md) before it hits the UI.
- **Configuration**: The recording duration and active port are pulled from [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

### 4. User Interaction (Key Events)
```python
81:     def on_key(self, event):
82:         if event.key == ' ':
83:             if not self.saving:
85:                 self.vis_buffer.clear()
86:                 self.saving = True
87:                 self.current_sample_data = []
```
-   **Line 82-87**: Listens for the SPACE key. When pressed, it resets the internal state to begin a clean recording session for the specified activity.

### 5. Data Persistence
```python
125:     def save_sample(self):
126:         self.saving = False
130:         path = os.path.join(settings.RAW_DATA_DIR, self.activity)
131:         os.makedirs(path, exist_ok=True)
134:         df = pd.DataFrame(self.current_sample_data)
137:         filename = os.path.join(path, f"{self.activity}_{int(time.time())}.csv")
138:         df.to_csv(filename, index=False, header=False)
```
-   **Line 134-138**: Uses `pandas` to convert the list of arrays into a CSV file. The file is saved in a subfolder named after the activity (e.g., `data/raw/walk/walk_1710543210.csv`). Note that `header=False` is used because this format expects raw amplitude columns only.

---

## 🎯 Key Takeaways
-   **Multithreading**: Essential for high-speed UART (921600 baud) to prevent the OS serial buffer from overflowing while the Python GIL is busy with Matplotlib rendering.
-   **Visual Feedback**: By seeing the signal *before* recording, the developer can ensure the environment is "quiet" (no external movement) before capturing baseline "empty" data.
-   **Labeling**: The script handles folder-based labeling automatically, which simplifies the subsequent `DataLoader` operations.

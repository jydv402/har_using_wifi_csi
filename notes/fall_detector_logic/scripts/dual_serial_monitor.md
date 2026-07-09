# Textbook:
## 📦 Library Reference

### External Libraries
- **`tkinter` (tk, ttk, scrolledtext)**: The Desktop GUI Window manager.
    - **Usage**: Creates the windows, buttons, and scrolling text areas that make the monitor easy to use.
- **`serial` (PySerial)**: The core communication engine.
- **`threading`**: Allows the script to monitor two USB ports at the same time without the window freezing.
- **`collections.deque`**: A specialized "First-In-First-Out" (FIFO) list.
    - **Usage**: Stores the last few lines of data to ensure they are displayed in the correct order.

### Local Dependencies
- **(None)**: Designed as a standalone hardware debugger.

## 📖 Overview
In this project, two ESP32s (TX and RX) must talk to each other perfectly. The `dual_serial_monitor.py` is a specialized "Two-Way Radio Scanner" that lets you watch both devices on one screen to make sure they are synching correctly. It allows you to monitor and log two independent serial ports (usually a TX node and an RX node) simultaneously. This is critical for debugging the handshake and timing between the two ESP32 devices. It features independent baud rate settings, live logging to text files, and a "Split-Pane" layout for side-by-side comparison.

---

## 💻 Code Walkthrough

### 1. The `SerialPanel` Class (Individual Monitor)
```python
15: class SerialPanel(ttk.Frame):
16:     def __init__(self, parent, title, log_filename, default_baud="115200"):
17:         super().__init__(parent)
20:         self.log_filename = log_filename
23:         self.line_buffer = []
24:         self.max_display_lines = 2000
```
-   **Line 16-20**: Each panel is a self-contained frame. It manages its own log file (e.g., `log_TX.txt`).
-   **Line 23-24**: The `line_buffer` acts as a temporary storage for incoming text. To keep the UI responsive, we don't update the screen for *every* character; instead, we batch them. The `max_display_lines` prevents the GUI from consuming infinite memory.

### 2. Connection Logic
```python
77:     def connect(self):
85:             self.serial_conn = serial.Serial(port, int(baud), timeout=1)
86:             self.is_reading = True
92:             self.thread = threading.Thread(target=self.read_from_port, daemon=True)
93:             self.thread.start()
```
-   **Line 85**: Opens the hardware serial port.
-   **Line 92-93**: Spawns a dedicated background thread for this specific COM port. Since we are monitoring two ESP32s, we have **two independent reader threads** running concurrently.

### 3. Threaded Data Reading
```python
106:     def read_from_port(self):
107:         while self.is_reading and self.serial_conn and self.serial_conn.is_open:
109:                 if self.serial_conn.in_waiting:
110:                     line_bytes = self.serial_conn.readline()
112:                         line_str = line_bytes.decode('utf-8', errors='replace').strip()
114:                         if self.save_to_log.get():
115:                             with open(self.log_filename, "a", encoding="utf-8") as f:
116:                                 f.write(line_str + "\n")
119:                         self.line_buffer.append(line_str)
```
-   **Line 110-112**: Reads a full line of text from the ESP32. `errors='replace'` is used because serial data can often be corrupted during a baud-rate switch or if the wires are loose.
-   **Line 115-116**: Appends the clean string to the log file on disk immediately.
-   **Line 119**: Adds the string to the `line_buffer` for the GUI thread to eventually pick up.

### 4. Periodic UI Refresh (Optimized)
```python
145:     def periodic_ui_update(self):
147:         if self.line_buffer:
149:             lines_to_add = self.line_buffer
150:             self.line_buffer = []
152:             content = "\n".join(lines_to_add) + "\n"
153:             self.text_area.insert(tk.END, content)
160:             self.text_area.see(tk.END)
163:         self.after(100, self.periodic_ui_update)
```
-   **Line 145-163**: This is the heart of the "lag-free" monitor. 
    1.  It checks if the `line_buffer` has data every 100ms.
    2.  It swaps the buffer out and joins all lines into a single large block of text.
    3.  `text_area.insert` is called once per refresh, which is 100x faster than calling it for every single line.
    4.  `self.after(100, ...)` schedules the next check, creating a loop within the Tkinter event system.

---

---

## 🎓 Concept Deep-Dives

### 1. Serial Handshakes & Protocols
When two hardware devices talk, they often use a "Question and Answer" pattern.
- **Goal**: By watching both COM ports at once, you can see if the RX node sent a command and if the TX node ignored it. This helps debug "Silent Hardware" issues that standard monitors would miss.

### 2. UI Batching (Performance)
Updating a computer screen is much slower than reading a serial port.
- **The Problem**: If you update the screen every time a single letter arrives, the whole computer will freeze.
- **The Solution (Line 160)**: We use a **Batching Queue**. We collect 100ms of data in the background, then "Dump" it all to the screen at once in the next UI tick. This makes the monitor feel fast and responsive.

---

## 🔗 Related Notes & Dependencies
- **Utility**: Serves as a diagnostic tool for the [rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md) and [tx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/tx_node.md).
- **Backend**: Uses the same logic found in `SerialReader` but applied to dual ports.

## 🎯 Key Takeaways
-   **Batching**: Never update a GUI widget directly from a high-speed serial thread. Always use a buffer and a timer.
-   **Thread Safety**: While `list.append` is thread-safe in Python, the logic of "swapping" the buffer at Line 149 ensures that the reader thread and the UI thread don't fight over the same data.
-   **Logging**: By logging to disk in real-time, you ensure that even if the app crashes, your debug data is saved.

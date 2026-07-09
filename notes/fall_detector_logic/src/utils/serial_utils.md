# Textbook: `src/utils/serial_utils.py`

## 📦 Library Reference

### External Libraries
- **`serial` (PySerial)**: The fundamental tool for hardware communication.
    - **Usage**: Opens the USB connection (`serial.Serial`), configures baud rates, and performs the raw `readline()` operations that grab text from the ESP32.
- **`threading`**: Allows Python to do two things at once.
    - **Usage**: Spawns the `_read_loop` as a separate "worker" so that the CPU never gets bored while waiting for the next radio packet.
- **`queue`**: A "Waiting Room" for data.
    - **Usage**: Safely passes packets from the background Serial thread to the main Python script without causing data corruption.
- **`time`**: Used for precision timers and thread delays.

### Local Dependencies
- **(None)**: This is a standalone utility designed to be as simple and robust as possible.

## 📖 Overview
Computers and ESP32s speak through a virtual "Wire" called Serial. The `AsyncSerialReader` is a high-speed listener that handles the messy job of catching Wi-Fi data at 100Hz without slowing down the rest of your program.
 Since Wi-Fi CSI data arrives at **100 packets per second** at a extremely high baud rate (921,600 bits/sec), a normal "Synchronous" reader would cause the application to freeze or lag. This class uses **Multithreading** and a **Priority Queue** to ensure zero data loss.

---

## 💻 Code Walkthrough

### 1. The Async Architecture
```python
11:     def __init__(self, port, baud_rate=921600, timeout=1):
18:         self.data_queue = queue.Queue(maxsize=10000)
```
-   **Line 11**: Sets the baud rate to `921600`. This is 8 times faster than the standard `115200`, which is necessary because each CSI packet is quite large.
-   **Line 18**: Initializes a `queue.Queue`. This is a thread-safe "Post Office Box". The serial thread drops data in, and the main thread picks it up whenever it's ready. A `maxsize=10000` ensures that if the program stops processing, the computer's memory doesn't overflow.

### 2. The Background Worker
```python
35:     def _read_loop(self):
36:         while self.is_running and self.serial_conn and self.serial_conn.is_open:
38:                 line = self.serial_conn.readline()
40:                     decoded = line.decode('utf-8', errors='ignore').strip()
41:                     if decoded.startswith("CSI_DATA"):
43:                             self.data_queue.put_nowait(decoded)
```
-   **Line 35-43**: This function runs in a separate thread. It spends 100% of its time waiting for the next line from the ESP32.
-   **Line 40**: `errors='ignore'` is used because sometimes the serial connection "garbage" characters are sent if the wire is touched. We simply ignore those bits.
-   **Line 43**: `put_nowait` ensures that if the queue *is* full, the script doesn't hang; it simply drops the packet and keeps moving.

### 3. Queue Consumption
```python
65:     def get_lines(self, max_lines=None):
69:         while not self.data_queue.empty():
73:                 lines.append(self.data_queue.get_nowait())
```
-   **Line 65-73**: This is called by scripts like the `InferenceDashboard`. It "drains" the queue. By returning a list of lines at once, we reduce the overhead of cross-thread communication.

---

---

## 🎓 Concept Deep-Dives

### 1. Why use Multithreading?
If your program does everything in one line (single thread), it can only do one thing at a time.
- **The Problem**: If the program is busy "Thinking" about an AI prediction, it might miss the data coming in from the USB port.
- **The Solution (Line 53)**: We create a **Background Thread**. This thread does nothing but listen to the serial port. Even if the main program freezes for a second, the background thread keeps catching the Wi-Fi data and putting it in a "Queue" (waiting room).

### 2. What is Baud Rate?
**Baud Rate** is the "Speed Limit" of the serial wire. 
- **The Standard**: 115,200 bits per second.
- **Our Setting (Line 11)**: **921,600**.
- **The Why**: CSI data is bulky. At standard speeds, the ESP32 transmitter would "choke" because it can't push the data out as fast as it records it. We use near-maximum speed to ensure a real-time 100Hz packet rate.

---

## 🔗 Related Notes & Dependencies
- **Firmware Source**: This reader is designed to communicate with the [rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md).
- **Consumer**: The data collected here is sent to the [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md) for processing.
- **Configuration**: The COM port and baud rate are pulled from [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

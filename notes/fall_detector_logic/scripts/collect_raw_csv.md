# Textbook:## 📦 Library Reference

### External Libraries
- **`pandas` (as `pd`)**: Used for file writing.
    - **Usage**: Efficiently writes the high-speed data stream into CSV format.
- **`numpy` (as `np`)**: Used for array manipulation.
- **`argparse`**: Handles terminal arguments for `--port` and `--activity`.

### Local Dependencies
- **[src.utils.serial_utils](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md)**: Used to launch the `AsyncSerialReader`.
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: Translates the incoming text into amplitudes.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides the global directory paths for raw data.

## 📖 Overview
The `collect_raw_csv.py` script is a high-performance recording tool. Unlike the general collector, this script focuses on speed and metadata, ensuring every single Wi-Fi packet is archived exactly as it arrived for later research. Unlike `collect_data.py`, which saves only the amplitudes, this script saves both the **Timestamp** and **RSSI** (Received Signal Strength Indicator) for every single packet. This is particularly useful for debugging signal quality or identifying long-term interference patterns.

---

## 💻 Code Walkthrough

### 1. Structure of a Raw Packet
```python
14: class RawCSVCollector:
20:     def __init__(self, port, activity, duration):
26:         self.collected_data = []
29:         self.target_packets = settings.CSI_PACKET_RATE * self.duration
```
-   **Line 26**: Stores all incoming data in a simple Python list. This is efficient for sequential collection of a single fixed-duration session.
-   **Line 29**: Uses the `duration` argument to calculate when to stop (defaulting to the value in `settings.py`).

### 2. Main Collection Loop
```python
44:             while self.reader.is_running and packet_count < self.target_packets:
45:                 lines = self.reader.get_lines(max_lines=100)
46:                 for line in lines:
47:                     parsed = self.parser.parse_line(line)
48:                     if parsed:
51:                         row = [
52:                             time.time(),           # Local PC Timestamp
53:                             parsed["rssi"],        # RSSI
54:                         ]
57:                         row.extend(parsed["amplitudes"].tolist())
59:                         self.collected_data.append(row)
```
-   **Line 44**: The loop continues until either the timeout is reached or the user stops it manually (Ctrl+C).
-   **Lines 51-57**: Constructs a "flat" list for the CSV row. 
    1.  Index 0: Unix timestamp (High precision).
    2.  Index 1: Signal strength in dBm.
    3.  Indices 2-115: Amplitudes for each of the 114 subcarriers.

### 3. Progress Tracking
```python
63:                         if packet_count % 100 == 0:
64:                             elapsed = time.time() - start_time
65:                             rate = packet_count / elapsed if elapsed > 0 else 0
66:                             print(f"\rCollected {packet_count}/{self.target_packets} packets "
67:                                   f"[{rate:.1f} pkts/s]", end="")
```
-   **Lines 63-67**: Provides a terminal progress bar. Printing the `rate` (packets per second) is critical for verifying that the ESP32 is actually hitting the target frequency (100Hz). If the rate drops to 50pkts/s, it indicates a bottleneck in the serial port or a bad Wi-Fi environment.

### 4. Saving with Headers
```python
92:         columns = ["timestamp", "rssi"]
93:         columns.extend([f"subcarrier_{i}" for i in range(settings.SUBCARRIERS)])
96:         df = pd.DataFrame(self.collected_data, columns=columns)
99:         filename = os.path.join(path, f"{self.activity}_raw_{int(time.time())}.csv")
100:         df.to_csv(filename, index=False)
```
-   **Lines 92-93**: Dynamically generates headers. The `DataLoader` uses these headers later to auto-detect which format the CSV is in.
-   **Line 100**: Unlike `collect_data.py`, this script saves with a **header row**, making the CSV self-documenting for tools like Excel or Pandas.

---

---

## 🎓 Concept Deep-Dives

### 1. Why log Raw CSI?
Most scripts process the data into "Amplitudes" immediately.
- **The Problem**: If you later realize your math was wrong, you can't undo the amplitude conversion.
- **The Solution (Line 85)**: This script saves the **Raw I/Q Strings** exactly as they came from the ESP32. This is like a "Security Camera" recording. You can "Replay" this raw data later using different parsers or preprocessing techniques without ever needing the original device again.

---

## 🔗 Related Notes & Dependencies
- **Hardware Source**: Logs data directly from the [rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md).
- **Processing**: This raw data can be processed later by the [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md).
- **Configuration**: Uses the `BAUD_RATE` defined in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

---

## 🎯 Key Takeaways
-   **Metadata Matters**: Saving the RSSI alongside the CSI allows for "Power-based Filtering" where weak packets are ignored before they can corrupt the ML model's weights.
-   **Sync vs Async**: While the serial reader is async, this script's *writing* to the list is synchronous within the main loop. This is acceptable here because there is no GUI (Matplotlib) competing for resources.
-   **Flexibility**: The system can distinguish between these "Raw" files and "Clean" files during training by checking for the `subcarrier_0` column name.

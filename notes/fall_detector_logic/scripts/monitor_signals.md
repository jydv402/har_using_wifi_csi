# Textbook: `scripts/monitor_signals.py`
## 📦 Library Reference

### External Libraries
- **`matplotlib` (`plt`, `animation`)**: The visual foundation of the diagnostic tool.
    - **Usage**: Renders the 2D Heatmap (Waterfall Plot) and the RSSI line graphs. `animation.FuncAnimation` ensures the signal updates in real-time at over 20 frames per second.
- **`numpy` (as `np`)**: The mathematical glue.
    - **Usage**: Manages the large 2D arrays (matrices) that represent the signal history for the heatmap visualization.
- **`threading`**: Crucial for real-time responsiveness.
    - **Usage**: Runs the serial data collector in the background so the GUI graphs never lag or skip frames.
- **`argparse`**: Handles terminal inputs.
    - **Usage**: Allows the user to specify `--port` and `--duration` without editing the code.

### Local Dependencies
- **[src.utils.serial_utils](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md)**: Connects to the ESP32.
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: Converts raw serial text into structured subcarrier data.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides critical constants مانند `CSI_PACKET_RATE` (100Hz).

## 📖 Overview
The `monitor_signals.py` is the most powerful diagnostic tool in the project. It provides a visual "Health Check" of your Wi-Fi environment, allowing you to see radio wave ripples that are invisible to the human eye.
While the `inference_dashboard` tells you "what the person is doing", this script tells you "**how well the Wi-Fi is performing**". It provides four distinct perspectives:
1.  **Subcarrier Heatmap**: Shows the intensity of all 114 subcarriers over time.
2.  **Amplitude Traces**: Shows detailed waveforms for 6 selected subcarriers.
3.  **RSSI Tracker**: Monitors overall signal strength.
4.  **Signal Quality Panel**: Calculates packet rates and error counts.

---

## 💻 Code Walkthrough

### 1. Visualization Setup (Heatmap)
```python
79:         self.heatmap_img = self.ax_heatmap.imshow(
80:             self.amp_history, aspect='auto', cmap='inferno',
81:             origin='lower', norm=Normalize(vmin=0, vmax=50),
82:             interpolation='bilinear'
83:         )
```
-   **Line 79-83**: Configures the 2D Heatmap.
    -   `cmap='inferno'`: Uses a dark-to-bright color scale (black -> purple -> orange -> yellow).
    -   `norm=Normalize(vmin=0, vmax=50)`: Constrains the color intensity to expected amplitude ranges, ensuring that strong signals don't "wash out" the visualization.
    -   `interpolation='bilinear'`: Smooths the pixels between subcarriers, making it easier to see physical patterns like "fading".

### 2. Live Buffer Management
```python
178:                     # Append to heatmap buffer
179:                     self.amp_history[self.amp_head] = amp
180:                     self.amp_head = (self.amp_head + 1) % self.history_length
181:                     self.amp_count = min(self.amp_count + 1, self.history_length)
```
-   **Line 178-181**: Implements a **Circular Buffer** for the amplitudes. Instead of shifting a massive NumPy array 100 times a second (which is slow), we simply update one row and move the "head" index.

### 3. Reordering for Display
```python
202:         ordered = np.vstack((
203:             self.amp_history[self.amp_head:],
204:             self.amp_history[:self.amp_head]
205:         ))[-self.amp_count:]
206:         self.heatmap_img.set_data(ordered)
```
-   **Line 202-205**: When it's time to draw the screen, we "unroll" the circular buffer so that the oldest data is at the top and the newest is at the bottom. This creates the "scrolling" waterfall effect.

### 4. Signal Health Analytics
```python
246:         recent = [t for t in self.packet_timestamps if now - t < 1.0]
247:         pkt_rate = len(recent)
265:         if pkt_rate >= 80:
266:             quality = "🟢 EXCELLENT"
274:         stats = (
275:             f"  Signal Quality: {quality}\n\n"
276:             f"  Packet Rate:     {pkt_rate:>4d} / {settings.CSI_PACKET_RATE} Hz\n"
)
```
-   **Line 246-247**: Calculates the "Real-time Frequency". It counts how many timestamps were recorded in the last 1.0 seconds. 
-   **Line 265-285**: Generates the text-based status report. This is where you can quickly see if the system is dropping packets (e.g., if the ESP32 is too far from the router).

---

---

## 🎓 Concept Deep-Dives

### 1. Reading a CSI Heatmap
The heatmap visualization (Line 250) is often called a "Waterfall Plot."
- **Color = Energy**: Bright colors (Yellow/White) mean the signal at that frequency is strong. Dark colors (Purple/Black) mean the signal is being blocked.
- **Motion Patterns**: When a person moves, you will see "Ripples" or "Wavy Lines" throughout the heatmap. A fall looks like a sudden, chaotic "Splash" across all subcarriers.

### 2. RSSI vs CSI Diagnostic
Why monitor both?
- **RSSI**: Tells you if the nodes are too far apart. If RSSI is -90dBm, your signal is "whispering," and the sensors won't work.
- **CSI**: Tells you what's happening *inside* the signal. Even if the RSSI is perfect, the CSI might show "Flatlines" if the room is perfectly still, or "Static" if there's interference.

---

## 🔗 Related Notes & Dependencies
- **Hardware Source**: Visualizes the stream coming from the [rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md).
- **Communication**: Uses the [serial_utils.md](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md) to catch the 100Hz packet stream.
- **Filtering**: Shows you which packets are being rejected based on the thresholds in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

## 🎯 Key Takeaways
-   **Heatmap Patterns**: Horizontal lines in the heatmap represent one subcarrier is blocked. Diagonal "waves" represent a person moving through the field (Multipath variations).
-   **Zero Signals**: If the heatmap is black, it means the Serial configuration is correct, but the ESP32 is not receiving any CSI-enabled packets from the TX node.
-   **Buffer Efficiency**: Circular buffers are essential for Matplotlib applications to maintain a high Frame Rate (FPS) without lag.

import os
import sys
import time
import argparse
import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation

if os.name == 'nt':
    import winsound

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.serial_utils import AsyncSerialReader
from src.data.parser import CSIParser, CSIRingBuffer
from config import settings

class DataCollector:
    def __init__(self, port, activity, auto_count=0):
        self.port = port
        self.activity = activity
        self.reader = AsyncSerialReader(port, settings.BAUD_RATE)
        self.parser = CSIParser()
        # Visualization ring buffer — window_size=100 means has_window() triggers after 100 packets
        self.vis_buffer = CSIRingBuffer(window_size=100, features=settings.FEATURES)
        self.saving = False
        self.collected_samples = 0
        self.auto_count = auto_count
        self.current_sample_data = []
        self.target_packets = settings.CSI_PACKET_RATE * settings.SAMPLE_DURATION

        # Diagnostic Metrics
        self.hz = 0
        self.packet_timestamps = []
        self.total_packets_received = 0

        # Setup plot
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.lines = [self.ax.plot([], [], lw=1)[0] for _ in range(settings.SUBCARRIERS)]
        self.ax.set_ylim(0, 100) # Slightly higher limit for HT20 amplitudes
        self.ax.set_xlim(0, 200)
        self.ax.set_xlabel("Time (packets)")
        self.ax.set_ylabel("Amplitude")

        # Prominent status label overlaid on the plot
        self.status_text = self.ax.text(
            0.5, 0.95, f"[{self.activity.upper()}] MONITORING: Press SPACE to Record | 'q' to Quit",
            transform=self.ax.transAxes, ha='center', va='top',
            fontsize=12, fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='steelblue', alpha=0.9)
        )

        # Connect key press event
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
    def start(self):
        self.reader.start()
        # Start the processing thread
        self.process_thread = threading.Thread(target=self.process_loop, daemon=True)
        self.process_thread.start()
        
        # Start animation
        # interval=30 for smoother visualization at 100Hz
        ani = animation.FuncAnimation(self.fig, self.update_plot, interval=30, blit=False, cache_frame_data=False)
        
        # If in auto mode, start the first recording after a short delay to allow system to stabilize
        if self.auto_count > 0:
            self.fig.canvas.manager.window.after(2000, self.start_recording)

        plt.show()

    def stop(self):
        self.reader.stop()
        if hasattr(self, 'process_thread'):
            self.process_thread.join(timeout=1.0)
        print("Data collection stopped.")

    def process_loop(self):
        while self.reader.is_running:
            lines = self.reader.get_lines(max_lines=100)
            for line in lines:
                parsed = self.parser.parse_line(line)
                if parsed:
                    amp = parsed["amplitudes"]
                    self.vis_buffer.append(amp)
                    
                    # Update diagnostic rate tracking
                    now = time.time()
                    self.packet_timestamps.append(now)
                    self.total_packets_received += 1
                    # Keep last 1 second for Hz calculation
                    self.packet_timestamps = [t for t in self.packet_timestamps if now - t <= 1.0]
                    self.hz = len(self.packet_timestamps)

                    if self.saving:
                        # IMPORTANT: Sync format with UniversalDataLoader expectations
                        # [0:timestamp, 1:rssi, 2:noise_floor, 3:agc, 4:fft, 5-56:subcarriers]
                        row = [time.time(), parsed["rssi"], parsed["noise_floor"], parsed["agc_gain"], parsed["fft_gain"]] + amp.tolist()
                        self.current_sample_data.append(row)
                        if len(self.current_sample_data) >= self.target_packets:
                            self.save_sample()
            time.sleep(0.01)

    def on_key(self, event):
        if event.key == ' ':
            if not self.saving:
                self.start_recording()
        elif event.key == 'q':
            plt.close()

    def start_recording(self):
        if self.saving: return
        
        print(f"\n--- Starting to record sample {self.collected_samples + 1} for '{self.activity}' ---")
        # Clear the visualization buffer to explicitly show the start of a clear recording window
        self.vis_buffer.clear()
        self.saving = True
        self.current_sample_data = []
        self.status_text.set_text(f"[RECORDING] Sample {self.collected_samples + 1}...")
        self.status_text.set_bbox(dict(boxstyle='round,pad=0.5', facecolor='darkred', alpha=0.9))
        self.fig.canvas.draw_idle()

    def update_plot(self, frame):
        # Draw as soon as we have any data
        if self.vis_buffer.count > 0:
            data = self.vis_buffer.buffer.copy()
            head = self.vis_buffer.head
            n_rows = min(self.vis_buffer.count, self.vis_buffer.window_size * 2)

            # Reorder for visualization (rolling window view)
            recent = np.vstack((data[head:], data[:head]))[-n_rows:]

            for i, line in enumerate(self.lines):
                if i < recent.shape[1]:
                    line.set_data(np.arange(len(recent)), recent[:, i])

            self.ax.set_xlim(0, max(200, len(recent)))

            # Update status text
            if not self.saving:
                self.status_text.set_text(
                    f"[{self.activity.upper()}] Rate: {self.hz}Hz | Packets: {self.total_packets_received}\nPress SPACE to Record"
                )
                self.status_text.set_bbox(dict(boxstyle='round,pad=0.5', facecolor='steelblue', alpha=0.9))
            else:
                # Show live progress count while recording
                done = len(self.current_sample_data)
                total = self.target_packets
                percent = int((done / total) * 100)
                self.status_text.set_text(f"[RECORDING] {percent}% ({done}/{total} packets)")
                self.status_text.set_bbox(dict(boxstyle='round,pad=0.5', facecolor='darkred', alpha=0.9))

    def save_sample(self):
        self.saving = False
        self.collected_samples += 1
        
        # Ensure directory exists
        path = os.path.join(settings.RAW_DATA_DIR, self.activity)
        os.makedirs(path, exist_ok=True)
        
        # Create DataFrame
        df = pd.DataFrame(self.current_sample_data)
        
        # Save to CSV
        filename = os.path.join(path, f"{self.activity}_{int(time.time())}.csv")
        df.to_csv(filename, index=False, header=False)
        print(f"Saved {len(self.current_sample_data)} packets to {filename}")
        self.status_text.set_text(f"[SAVED] Sample {self.collected_samples}! Ready for next.")
        self.status_text.set_bbox(dict(boxstyle='round,pad=0.5', facecolor='forestgreen', alpha=0.9))
        self.fig.canvas.draw_idle()

        # Play beep for audio feedback
        if os.name == 'nt':
            try:
                winsound.Beep(1000, 200) # 1kHz for 200ms
            except:
                pass

        # Check for auto-trigger
        if self.auto_count > 0:
            if self.collected_samples < self.auto_count:
                print(f"Auto-mode: Starting next sample in 1 second... ({self.collected_samples}/{self.auto_count})")
                self.fig.canvas.manager.window.after(1000, self.start_recording)
            else:
                print(f"Auto-mode: Finished collecting {self.auto_count} samples!")
                self.status_text.set_text(f"[FINISHED] Auto-Collection of {self.auto_count} samples!")
                self.fig.canvas.draw_idle()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect CSI Data with Visualization")
    parser.add_argument("--port", type=str, default=settings.SERIAL_PORT, help="Serial port of ESP32")
    parser.add_argument("--activity", type=str, required=True, choices=getattr(settings, 'DATA_FOLDERS', settings.CLASSES), help="Activity to record")
    parser.add_argument("--auto", type=int, default=0, help="Automatically collect N samples")
    
    args = parser.parse_args()
    
    collector = DataCollector(args.port, args.activity, auto_count=args.auto)
    try:
        collector.start()
    except KeyboardInterrupt:
        pass
    finally:
        collector.stop()

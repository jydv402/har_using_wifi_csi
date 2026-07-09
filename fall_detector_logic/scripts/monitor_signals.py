"""
Real-Time CSI Signal Monitor — HAR on ESP32 (Project V2)
=========================================================
A comprehensive visualization tool for monitoring WiFi CSI data in real-time.

Displays:
  1. Subcarrier Heatmap     — time × subcarrier amplitude matrix
  2. Amplitude Waterfall    — scrolling time-series of selected subcarriers
  3. RSSI Tracker           — rolling average and instantaneous RSSI
  4. Packet Rate Meter      — actual vs expected 100 Hz
  5. Signal Quality Stats   — dropped packets, parse errors

Usage:
    python scripts/monitor_signals.py --port COM3
    python scripts/monitor_signals.py --port COM3 --duration 60
"""

import os
import sys
import time
import argparse
import threading
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import Normalize
from collections import deque

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.serial_utils import AsyncSerialReader
from src.data.parser import CSIParser
from config import settings


class SignalMonitor:
    """
    Real-time CSI signal visualization tool with 4-panel dashboard.
    """
    def __init__(self, port, history_length=200):
        self.port = port
        self.history_length = history_length

        # Data structures
        self.reader = AsyncSerialReader(port, settings.BAUD_RATE)
        self.parser = CSIParser()

        # Amplitude history: (history_length × 52 subcarriers) heatmap buffer
        self.amp_history = np.zeros((history_length, settings.SUBCARRIERS), dtype=np.float32)
        self.amp_head = 0
        self.amp_count = 0

        # RSSI history
        self.rssi_history = deque(maxlen=history_length)

        # Packet rate tracking
        self.packet_timestamps = deque(maxlen=500)
        self.total_packets = 0
        self.parse_errors = 0
        self.total_lines = 0

        # Selected subcarriers for waterfall plot (show a representative subset)
        self.selected_subs = [0, 10, 20, 30, 40, 51]  # 6 subcarriers across the spectrum
        self.sub_colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(self.selected_subs)))

        # Setup figure
        self.fig = plt.figure(figsize=(14, 9))
        self.fig.suptitle("HAR-on-ESP32 — Real-Time CSI Signal Monitor", 
                         fontsize=14, fontweight='bold', color='white')
        self.fig.patch.set_facecolor('#1a1a2e')

        # Create grid: 2×2 layout
        gs = self.fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3,
                                    left=0.07, right=0.95, top=0.92, bottom=0.08)

        # Panel 1: Subcarrier Heatmap (top-left)
        self.ax_heatmap = self.fig.add_subplot(gs[0, 0])
        self.ax_heatmap.set_facecolor('#16213e')
        self.heatmap_img = self.ax_heatmap.imshow(
            self.amp_history, aspect='auto', cmap='inferno',
            origin='lower', norm=Normalize(vmin=0, vmax=50),
            interpolation='bilinear'
        )
        self.ax_heatmap.set_xlabel("Subcarrier Index", color='white', fontsize=9)
        self.ax_heatmap.set_ylabel("Time (packets)", color='white', fontsize=9)
        self.ax_heatmap.set_title("Subcarrier Heatmap", color='#e94560', fontsize=11)
        self.ax_heatmap.tick_params(colors='white', labelsize=7)
        cbar = self.fig.colorbar(self.heatmap_img, ax=self.ax_heatmap, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(colors='white', labelsize=7)
        cbar.set_label('Amplitude', color='white', fontsize=8)

        # Panel 2: Amplitude Waterfall (top-right)
        self.ax_waterfall = self.fig.add_subplot(gs[0, 1])
        self.ax_waterfall.set_facecolor('#16213e')
        self.waterfall_lines = []
        for i, sub_idx in enumerate(self.selected_subs):
            line, = self.ax_waterfall.plot([], [], lw=1.2, color=self.sub_colors[i],
                                           alpha=0.85, label=f"SC {sub_idx}")
        self.waterfall_lines.append(line)
        self.ax_waterfall.set_xlim(0, self.history_length)
        self.ax_waterfall.set_ylim(0, 60)
        self.ax_waterfall.set_xlabel("Time (packets)", color='white', fontsize=9)
        self.ax_waterfall.set_ylabel("Amplitude", color='white', fontsize=9)
        self.ax_waterfall.set_title("Subcarrier Amplitude Traces", color='#e94560', fontsize=11)
        self.ax_waterfall.tick_params(colors='white', labelsize=7)
        self.ax_waterfall.legend(loc='upper right', fontsize=6, ncol=3,
                                 facecolor='#16213e', edgecolor='#e94560', 
                                 labelcolor='white')

        # Panel 3: RSSI Tracker (bottom-left)
        self.ax_rssi = self.fig.add_subplot(gs[1, 0])
        self.ax_rssi.set_facecolor('#16213e')
        self.rssi_line, = self.ax_rssi.plot([], [], lw=1.5, color='#00d2ff', alpha=0.9)
        self.rssi_avg_line, = self.ax_rssi.plot([], [], lw=2, color='#e94560', 
                                                 alpha=0.9, linestyle='--', label='Avg (20)')
        self.ax_rssi.set_xlim(0, self.history_length)
        self.ax_rssi.set_ylim(-90, -30)
        self.ax_rssi.set_xlabel("Time (packets)", color='white', fontsize=9)
        self.ax_rssi.set_ylabel("RSSI (dBm)", color='white', fontsize=9)
        self.ax_rssi.set_title("RSSI Tracker", color='#e94560', fontsize=11)
        self.ax_rssi.tick_params(colors='white', labelsize=7)
        self.ax_rssi.axhline(y=settings.RSSI_FLOOR, color='red', linestyle=':', 
                             alpha=0.5, label=f'Floor ({settings.RSSI_FLOOR} dBm)')
        self.ax_rssi.legend(loc='upper right', fontsize=7, facecolor='#16213e', 
                            edgecolor='#e94560', labelcolor='white')

        # Panel 4: Stats Panel (bottom-right)
        self.ax_stats = self.fig.add_subplot(gs[1, 1])
        self.ax_stats.set_facecolor('#16213e')
        self.ax_stats.axis('off')
        self.ax_stats.set_title("Signal Quality", color='#e94560', fontsize=11)
        self.stats_text = self.ax_stats.text(
            0.5, 0.5, "Waiting for data...",
            transform=self.ax_stats.transAxes, ha='center', va='center',
            fontsize=11, color='white', fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#0f3460', alpha=0.9)
        )

        # Connect key press
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

    def start(self):
        self.reader.start()
        print(f"Monitoring CSI signals on {self.port} at {settings.BAUD_RATE} baud")
        print("Press 'q' to quit\n")

        # Start processing thread
        self.process_thread = threading.Thread(target=self.process_loop, daemon=True)
        self.process_thread.start()

        # Start animation at 20 FPS
        self.ani = animation.FuncAnimation(
            self.fig, self.update_plot, interval=50, blit=False, cache_frame_data=False
        )
        plt.show()

    def stop(self):
        self.reader.stop()
        if hasattr(self, 'process_thread'):
            self.process_thread.join(timeout=1.0)
        print("\nMonitor stopped.")

    def on_key(self, event):
        if event.key == 'q':
            plt.close()

    def process_loop(self):
        """Background thread: read serial, parse CSI, accumulate data."""
        while self.reader.is_running:
            lines = self.reader.get_lines(max_lines=200)
            for line in lines:
                self.total_lines += 1
                parsed = self.parser.parse_line(line)
                if parsed:
                    amp = parsed["amplitudes"]
                    rssi = parsed["rssi"]

                    # Append to heatmap buffer
                    self.amp_history[self.amp_head] = amp
                    self.amp_head = (self.amp_head + 1) % self.history_length
                    self.amp_count = min(self.amp_count + 1, self.history_length)

                    # Append RSSI
                    self.rssi_history.append(rssi)

                    # Track packet rate
                    self.packet_timestamps.append(time.time())
                    self.total_packets += 1
                else:
                    if line.startswith("CSI_DATA"):
                        self.parse_errors += 1

            time.sleep(0.005)

    def update_plot(self, frame):
        """Animation callback — update all 4 panels."""
        if self.amp_count == 0:
            return

        # ── Panel 1: Heatmap ──────────────────────────────────────────────
        # Reorder buffer so most recent is at the top
        ordered = np.vstack((
            self.amp_history[self.amp_head:],
            self.amp_history[:self.amp_head]
        ))[-self.amp_count:]
        self.heatmap_img.set_data(ordered)
        self.heatmap_img.set_extent([0, settings.SUBCARRIERS, 0, self.amp_count])

        # ── Panel 2: Waterfall traces ─────────────────────────────────────
        # Re-draw lines for selected subcarriers
        self.ax_waterfall.clear()
        self.ax_waterfall.set_facecolor('#16213e')
        for i, sub_idx in enumerate(self.selected_subs):
            trace = ordered[:, sub_idx] if sub_idx < ordered.shape[1] else np.zeros(len(ordered))
            self.ax_waterfall.plot(np.arange(len(trace)), trace, 
                                   lw=1.2, color=self.sub_colors[i],
                                   alpha=0.85, label=f"SC {sub_idx}")
        self.ax_waterfall.set_xlim(0, max(self.history_length, len(ordered)))
        self.ax_waterfall.set_ylim(0, max(60, np.max(ordered) * 1.1) if ordered.size > 0 else 60)
        self.ax_waterfall.set_xlabel("Time (packets)", color='white', fontsize=9)
        self.ax_waterfall.set_ylabel("Amplitude", color='white', fontsize=9)
        self.ax_waterfall.set_title("Subcarrier Amplitude Traces", color='#e94560', fontsize=11)
        self.ax_waterfall.tick_params(colors='white', labelsize=7)
        self.ax_waterfall.legend(loc='upper right', fontsize=6, ncol=3,
                                 facecolor='#16213e', edgecolor='#e94560', labelcolor='white')

        # ── Panel 3: RSSI ─────────────────────────────────────────────────
        if len(self.rssi_history) > 0:
            rssi_arr = np.array(self.rssi_history)
            x = np.arange(len(rssi_arr))
            self.rssi_line.set_data(x, rssi_arr)

            # Rolling average (window=20)
            if len(rssi_arr) >= 20:
                avg = np.convolve(rssi_arr, np.ones(20)/20, mode='valid')
                self.rssi_avg_line.set_data(np.arange(19, 19 + len(avg)), avg)
            
            self.ax_rssi.set_xlim(0, max(self.history_length, len(rssi_arr)))
            y_min = min(rssi_arr.min() - 5, settings.RSSI_FLOOR - 10)
            y_max = max(rssi_arr.max() + 5, -30)
            self.ax_rssi.set_ylim(y_min, y_max)

        # ── Panel 4: Stats ────────────────────────────────────────────────
        # Calculate packet rate
        now = time.time()
        recent = [t for t in self.packet_timestamps if now - t < 1.0]
        pkt_rate = len(recent)

        # Calculate RSSI stats
        if len(self.rssi_history) > 0:
            rssi_arr = np.array(self.rssi_history)
            rssi_now = rssi_arr[-1]
            rssi_avg = rssi_arr.mean()
        else:
            rssi_now = 0
            rssi_avg = 0

        # Calculate mean amplitude
        if self.amp_count > 0:
            mean_amp = ordered.mean()
        else:
            mean_amp = 0

        # Signal quality rating
        if pkt_rate >= 80:
            quality = "🟢 EXCELLENT"
        elif pkt_rate >= 50:
            quality = "🟡 GOOD"
        elif pkt_rate >= 20:
            quality = "🟠 FAIR"
        else:
            quality = "🔴 POOR"

        stats = (
            f"  Signal Quality: {quality}\n\n"
            f"  Packet Rate:     {pkt_rate:>4d} / {settings.CSI_PACKET_RATE} Hz\n"
            f"  Total Packets:   {self.total_packets:>6d}\n"
            f"  Parse Errors:    {self.parse_errors:>6d}\n\n"
            f"  RSSI Current:    {rssi_now:>4.0f} dBm\n"
            f"  RSSI Average:    {rssi_avg:>4.1f} dBm\n"
            f"  Mean Amplitude:  {mean_amp:>5.1f}\n\n"
            f"  Subcarriers:     {settings.SUBCARRIERS}\n"
            f"  Bandwidth:       HT20 (20 MHz)\n"
            f"  Window Size:     {settings.WINDOW_SIZE} pkts"
        )
        self.stats_text.set_text(stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time CSI Signal Monitor")
    parser.add_argument("--port", type=str, default=settings.SERIAL_PORT,
                        help="Serial port of ESP32 Receiver")
    parser.add_argument("--history", type=int, default=200,
                        help="Number of packets to display in history")

    args = parser.parse_args()

    monitor = SignalMonitor(args.port, history_length=args.history)
    try:
        monitor.start()
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()

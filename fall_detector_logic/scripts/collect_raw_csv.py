import os
import sys
import time
import argparse
import pandas as pd
import numpy as np

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.serial_utils import AsyncSerialReader
from src.data.parser import CSIParser
from config import settings

class RawCSVCollector:
    """
    Collects raw CSI data from the ESP32 and saves it sequentially into a standard CSV format.
    The resulting CSV file will contain the metadata fields as columns, 
    and the 52 subcarrier amplitudes as the final columns.
    """
    def __init__(self, port, activity, duration):
        self.port = port
        self.activity = activity
        self.duration = duration
        self.reader = AsyncSerialReader(port, settings.BAUD_RATE)
        self.parser = CSIParser()
        self.collected_data = []

        # Calculate target packets based on duration and expected packet rate
        self.target_packets = settings.CSI_PACKET_RATE * self.duration

    def start(self):
        print(f"\n--- Starting Raw CSV Data Collection ---")
        print(f"Activity: {self.activity.upper()}")
        print(f"Target Duration: {self.duration} seconds (~{self.target_packets} packets)")
        print(f"Port: {self.port} at {settings.BAUD_RATE} baud")
        print("Listening for data... (Press Ctrl+C to stop early)")
        
        self.reader.start()
        
        start_time = time.time()
        packet_count = 0
        
        try:
            while self.reader.is_running and packet_count < self.target_packets:
                lines = self.reader.get_lines(max_lines=100)
                for line in lines:
                    parsed = self.parser.parse_line(line)
                    if parsed:
                        # Flatten the parsed data into a single row
                        # Metadata first, then the 52 subcarrier amplitudes
                        row = [
                            time.time(),           # Local PC Timestamp
                            parsed["rssi"],        # RSSI
                            parsed["noise_floor"], # Noise Floor
                            parsed["agc_gain"],    # AGC Gain
                            parsed["fft_gain"],    # FFT Gain
                        ]
                        
                        # Add the 52 subcarrier amplitudes
                        row.extend(parsed["amplitudes"].tolist())
                        
                        self.collected_data.append(row)
                        packet_count += 1
                        
                        # Print progress every 100 packets
                        if packet_count % 100 == 0:
                            elapsed = time.time() - start_time
                            rate = packet_count / elapsed if elapsed > 0 else 0
                            print(f"\rCollected {packet_count}/{self.target_packets} packets "
                                  f"[{rate:.1f} pkts/s]", end="")
                            
                time.sleep(0.01) # Small sleep to prevent 100% CPU usage
                
        except KeyboardInterrupt:
            print("\nCollection stopped manually by user.")
            
        finally:
            self.stop()
            self.save_csv()

    def stop(self):
        self.reader.stop()

    def save_csv(self):
        print("\n\nSaving data...")
        if not self.collected_data:
            print("No valid CSI data was collected. Nothing to save.")
            return

        # Ensure directory exists
        path = os.path.join(settings.RAW_DATA_DIR, self.activity)
        os.makedirs(path, exist_ok=True)
        
        # Create column names
        columns = ["timestamp", "rssi", "noise_floor", "agc_gain", "fft_gain"]
        columns.extend([f"subcarrier_{i}" for i in range(settings.SUBCARRIERS)])
        
        # Create DataFrame
        df = pd.DataFrame(self.collected_data, columns=columns)
        
        # Save to CSV
        filename = os.path.join(path, f"{self.activity}_raw_{int(time.time())}.csv")
        df.to_csv(filename, index=False)
        print(f"✅ Successfully saved {len(self.collected_data)} packets to:")
        print(f"-> {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect Raw CSI Data to CSV")
    parser.add_argument("--port", type=str, default=settings.SERIAL_PORT, help="Serial port of ESP32")
    parser.add_argument("--activity", type=str, required=True, choices=getattr(settings, 'DATA_FOLDERS', settings.CLASSES), help="Activity to record")
    parser.add_argument("--duration", type=int, default=settings.SAMPLE_DURATION, help="How many seconds to record")
    
    args = parser.parse_args()
    
    collector = RawCSVCollector(args.port, args.activity, args.duration)
    collector.start()

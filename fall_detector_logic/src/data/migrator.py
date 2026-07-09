
import os
import sys
import pandas as pd
import numpy as np
import glob
from pathlib import Path

# Ensure we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import settings

class DataMigrator:
    """
    Imports WiFall fall data into the project's standardized CSV format.
    WiFall uses len=104 (52 I/Q pairs) which maps directly to our 52 subcarriers.
    """
    def __init__(self):
        self.output_dir = settings.RAW_DATA_DIR

    def migrate_wifall_fall(self, base_path):
        """
        Processes WiFall dataset — FALL class only.
        Structure: IDx/fall/*.csv
        WiFall header: type,seq,timestamp,...,rssi,...,noise_floor,...,len,...,data
        """
        print(f"Migrating WiFall fall data from {base_path}...")
        
        csv_files = glob.glob(str(Path(base_path) / "**" / "fall" / "*.csv"), recursive=True)
        print(f"Found {len(csv_files)} fall CSV files across all participants")
        
        success = 0
        skipped = 0
        
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            # Extract participant ID from path (e.g., ID1/fall/xxx.csv -> ID1)
            participant = Path(file_path).parent.parent.name
            out_name = f"wifall_{participant}_{filename}"
            
            if self._process_wifall_file(file_path, out_name):
                success += 1
            else:
                skipped += 1
        
        print(f"Migration complete: {success} files imported, {skipped} skipped")

    def _process_wifall_file(self, file_path, out_name):
        """Reads a WiFall CSV, extracts 52-subcarrier amplitudes, saves in our format."""
        try:
            df = pd.read_csv(file_path)
            if 'data' not in df.columns:
                print(f"  Skip (no data column): {file_path}")
                return False
            
            processed_rows = []
            for _, row in df.iterrows():
                rssi = int(row.get('rssi', -50))
                noise_floor = int(row.get('noise_floor', -95))
                data_str = str(row['data'])
                
                try:
                    # WiFall data format: "[I, Q, I, Q, ...]" with len=104 (52 pairs)
                    payload_str = data_str.strip('" []')
                    iq_values = np.fromstring(payload_str, sep=",", dtype=np.float32)
                    
                    num_pairs = len(iq_values) // 2
                    if num_pairs < 52:
                        continue
                    
                    i_vals = iq_values[0::2]
                    q_vals = iq_values[1::2]
                    amplitudes = np.sqrt(i_vals**2 + q_vals**2)
                    
                    if num_pairs == 52:
                        # WiFall len=104: already exactly 52 subcarriers
                        valid_amp = amplitudes[:52]
                    elif num_pairs >= 64:
                        # HT20 with 64 subcarriers: extract 52 valid
                        valid_indices = list(range(6, 32)) + list(range(33, 59))
                        valid_amp = amplitudes[valid_indices]
                    else:
                        continue
                    
                    # Build row in our format: [timestamp, rssi, nf, agc, fft, amp_0..amp_51]
                    entry = [0, rssi, noise_floor, 0, 0] + valid_amp.tolist()
                    processed_rows.append(entry)
                except Exception:
                    continue
            
            if not processed_rows:
                print(f"  Skip (no valid rows): {file_path}")
                return False
            
            # Save to RAW_DATA_DIR/fall/
            target_folder = self.output_dir / "fall"
            target_folder.mkdir(parents=True, exist_ok=True)
            
            columns = ["timestamp", "rssi", "noise_floor", "agc_gain", "fft_gain"] + \
                      [f"subcarrier_{i}" for i in range(settings.SUBCARRIERS)]
            out_df = pd.DataFrame(processed_rows, columns=columns)
            out_df.to_csv(target_folder / out_name, index=False)
            return True
            
        except Exception as e:
            print(f"  Error: {file_path}: {e}")
            return False

if __name__ == "__main__":
    migrator = DataMigrator()
    
    # WiFall is in reference/ directory (outside project_v3)
    ref_path = project_root.parent / "reference"
    
    wifall_path = ref_path / "WiFall"
    if wifall_path.exists():
        migrator.migrate_wifall_fall(wifall_path)
    else:
        print(f"WiFall not found at {wifall_path}")
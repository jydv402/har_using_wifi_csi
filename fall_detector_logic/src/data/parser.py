import numpy as np
from config import settings

class CSIParser:
    """
    Parser for Project V3 (Strict HT20 / 20MHz).
    Optimized for 52 valid data subcarriers from 64-point ESP32 CSI packets.
    """
    def __init__(self):
        # Usable subcarrier indices for HT20 (52 subcarriers)
        # Standard: 6-31 and 33-58 in a 64-length array
        self.ht20_valid_indices = list(range(6, 32)) + list(range(33, 59))

    def parse_line(self, line):
        """
        Robustly parses a CSI_DATA line and returns normalized amplitudes.
        Supports:
        - Bracketed: CSI_DATA,RSSI,x,...[v1,v2]
        - Key-Value: CSI_DATA,RSSI,x,SNR,y,LEN,z,DATA,v1,v2...
        """
        try:
            if "CSI_DATA" not in line:
                return None

            # 1. Split line to identify structure
            meta_parts = line.split(",")
            
            # 2. Extract RSSI (Keyword-aware or context-aware)
            rssi = None
            try:
                if "RSSI" in meta_parts:
                    idx = meta_parts.index("RSSI")
                    rssi = int(meta_parts[idx + 1])
                elif len(meta_parts) > 4:
                    # In: CSI_DATA,time,mac,rssi,...
                    # Index 3 is typical for the user's current RX log format
                    rssi = int(meta_parts[3])
                else:
                    # Legacy fallback
                    rssi = int(meta_parts[2])
            except:
                return None

            if rssi is not None and rssi < settings.RSSI_FLOOR:
                return None
                
            # Extract additional hardware metadata (Noise Floor, FFT Gain, AGC Gain)
            noise_floor = -95
            fft_gain = 0
            agc_gain = 0
            try:
                if len(meta_parts) > 7:
                    noise_floor = int(meta_parts[5])
                    fft_gain = int(meta_parts[6])
                    agc_gain = int(meta_parts[7])
            except Exception:
                pass

            # 3. Extract Payload (Bracket or DATA tag)
            if "[" in line:
                payload_str = line.split("[")[1].split("]")[0].strip()
            elif "DATA," in line:
                payload_str = line.split("DATA,")[1].strip()
            else:
                return None

            # 4. Parse IQ values
            iq_values = np.fromstring(payload_str, sep=",", dtype=np.int16)
            if len(iq_values) < 80: 
                return None
            
            # 4. Compute amplitudes (Combine I and Q)
            i_vals = iq_values[0::2].astype(np.float32)
            q_vals = iq_values[1::2].astype(np.float32)
            amplitudes = np.sqrt(i_vals**2 + q_vals**2)

            num_pairs = len(amplitudes)
            
            # Classify by packet length (Number of IQ Pairs)
            if 50 <= num_pairs <= 64: 
                # HT20 (64 pairs)
                if num_pairs == 64:
                    valid_amp = amplitudes[self.ht20_valid_indices]
                else:
                    valid_amp = amplitudes
            else:
                return None

            return {
                "rssi": rssi,
                "noise_floor": noise_floor,
                "fft_gain": fft_gain,
                "agc_gain": agc_gain,
                "amplitudes": valid_amp,
                "subcarrier_count": len(valid_amp)
            }

        except Exception:
            return None


class CSIRingBuffer:
    """
    A lock-free compatible circular buffer to accumulate parsed CSI amplitudes
    for sliding window ML inference.
    """
    def __init__(self, window_size, features=settings.FEATURES):
        self.window_size = window_size
        self.features = features
        # Double buffer size to handle overlaps safely
        self.buffer = np.zeros((window_size * 2, features), dtype=np.float32)
        self.head = 0
        self.count = 0

    def append(self, feature_array):
        """Add a new CSI packet to the buffer."""
        # Trim or pad to match required feature length
        if len(feature_array) > self.features:
            arr = feature_array[:self.features]
        elif len(feature_array) < self.features:
            arr = np.pad(feature_array, (0, self.features - len(feature_array)))
        else:
            arr = feature_array

        self.buffer[self.head] = arr
        self.head = (self.head + 1) % (self.window_size * 2)
        if self.count < self.window_size * 2:
            self.count += 1

    def has_window(self):
        return self.count >= self.window_size

    def get_recent_window(self):
        """Returns the most recent `window_size` samples."""
        if not self.has_window():
            return None
            
        # Extract the window, handling the circular wraparound
        start_idx = (self.head - self.window_size) % (self.window_size * 2)
        
        if start_idx < self.head:
            # Contiguous
            return self.buffer[start_idx:self.head].copy()
        else:
            # Wraparound
            return np.vstack((self.buffer[start_idx:], self.buffer[:self.head]))

    def advance_hop(self, hop_size):
        """Safely advance the buffer by hop_size to implement sliding window overlap.
        Reduces count so the buffer waits for `hop_size` more packets before the next window."""
        self.count = max(0, self.count - hop_size)

    def clear(self):
        self.head = 0
        self.count = 0

"""
Central configuration for CSI HAR System (Project V3)
ESP32 Architecture - HT20 (20MHz) ONLY
"""

from pathlib import Path

# ── Project Root ──────────────────────────────────────────────────────────────
# Resolves to the project_v3/ directory regardless of where scripts are run from.
_ROOT = Path(__file__).parent.parent

# ── Hardware ──────────────────────────────────────────────────────────────────
SERIAL_PORT    = "COM3"       # RX node USB serial port
BAUD_RATE      = 921600       # Must match har_csi_rx.ino

# TX node broadcasts UDP at 100 Hz → RX node picks up ~100 CSI frames/sec
CSI_PACKET_RATE = 100  # packets per second

# Strictly HT20 (20MHz)
CSI_LEN_BYTES  = 128   # Expected data->len in the RX CSI callback for HT20
CSI_RAW_PAIRS  = 64    # Total I/Q pairs per HT20 frame (128 bytes / 2)
SUBCARRIERS    = 52    # Valid subcarriers after guard bands and DC nulls for HT20
RSSI_FLOOR     = -85   # dBm — discard packets weaker than this (noise floor)

# ── Dynamic Features ──────────────────────────────────────────────────────────
# Toggle this to False if hardware metadata causes model instability
INCLUDE_METADATA = False
# If True: RSSI, Noise Floor, AGC, FFT + 52 subcarriers (56 features)
# If False: Backwards compatibility to HT20 subcarriers only (52 features)
FEATURES = 56 if INCLUDE_METADATA else SUBCARRIERS

# ── Data Collection ───────────────────────────────────────────────────────────
# 5-class setup — gives model explicit jump/run vs fall discrimination (v7.0)
CLASSES           = ["idle", "walk", "run", "jump", "fall"]

# Maps existing data folder names to the 5-class labels
DATA_FOLDERS      = ["empty", "stand", "walk", "sit", "fall", "run", "jump"]
CLASS_MAP         = {
    "empty": "idle",  "stand": "idle",  "sit": "idle",
    "walk": "walk",   "run": "run",
    "jump": "jump",   "fall": "fall",
}
SAMPLES_PER_CLASS = 50
SAMPLE_DURATION   = 10  # seconds per recorded sample

# ── Preprocessing ─────────────────────────────────────────────────────────────
WINDOW_SIZE    = 100    # CSI packets per input window (3.3 seconds at 30Hz)
HOP_SIZE       = 25     # Sliding window hop (75% overlap for smooth inference)
NORMALIZE      = True
APPLY_CLEANING = True   # Minimal cleaning: DC removal + median filter (v6.1)
DENOISE_KERNEL = 3      # Median filter kernel (must be odd)

# ── Inference & Probability ──────────────────────────────────────────────────
CONFIDENCE_THRESHOLD     = 0.7  # Reject predictions below 70%
INFERENCE_CONSENSUS_SIZE = 3    # Window consensus for stable status

# ── Model Architecture ────────────────────────────────────────────────────────
CNN_FILTERS    = [64, 128, 128]  # Three Conv1D blocks
CNN_KERNEL_SIZE = 3
GRU_UNITS      = [64, 32]
DENSE_UNITS    = [64, 32]
DROPOUT_RATE   = 0.3
USE_FOCAL_LOSS = True  # Enable focal loss to focus on minority Fall class

# ── Training ──────────────────────────────────────────────────────────────────
BATCH_SIZE               = 64
EPOCHS                   = 200
LEARNING_RATE            = 0.0003
EARLY_STOPPING_PATIENCE  = 25

# ── Augmentation (Safety Limits) ──────────────────────────────────────────────
# Enabled (v6.0) to solve room-specific overfitting and small dataset gap
AUG_MAX_SAMPLES_PER_CLASS = 5000   # Balanced target per class — avoids over-augmenting small single-folder classes
AUG_NOISE_SCALE  = 0.02   # 2% jitter (safe limit)
AUG_MAG_RANGE    = 0.10   # ±10% amplitude variation
AUG_SHIFT_MAX    = 5      # ±50ms temporal shift

# ── Inference ─────────────────────────────────────────────────────────────────
FALL_PROBABILITY_THRESHOLD = 0.70
CONSECUTIVE_DETECTIONS     = 3
MIN_ALERT_INTERVAL         = 60  # seconds between alerts

# ── Paths (absolute, portable) ────────────────────────────────────────────────
DATA_DIR           = _ROOT / "data"
RAW_DATA_DIR       = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODEL_DIR          = _ROOT / "models"
EVALUATION_DIR     = _ROOT / "evaluation"

# Technical Guide: Wi-Fi CSI Fall Detection System

This guide provides an in-depth look at the technical implementation of the Fall Detection system using Wi-Fi Channel State Information (CSI).

## 📡 CSI Data Pipeline

The pipeline is designed for high-throughput, low-latency processing of Wi-Fi Channel State Information (CSI).

### 1. Raw Data Collection (`src/data/parser.py`)
- **Source**: Serial stream from ESP32 RX node.
- **Format**: Raw CSI I/Q samples packaged as binary data.
- **Filtering**: Packets with RSSI below -85dBm are discarded as noise.

### 2. Preprocessing (`src/data/preprocessor.py`)
- **Outlier Removal**: Z-score based filtering to eliminate anomalous signal spikes.
- **Denoising**: Median filtering with a kernel size of 3 to smooth the CSI stream.
- **Normalization**: Standard scaling (Z-score) applied per-batch to ensure consistent feature range.

### 3. Windowing and Loading (`src/data/loader.py`)
- **Window Size**: 50 CSI packets (approx. 500ms at 100Hz).
- **Hop Size**: 25 packets (50% overlap) for temporal continuity.
- **Augmentation**: Synthetic data generation for minority classes (e.g., Fall).

---

## 🧠 Model Architecture

We employ a **CNN-GRU Hybrid** model, optimized for the spatial and temporal characteristics of CSI data.

### 1D-CNN Layers (Spatial)
- Extracts frequency-domain features across the 114 subcarriers.
- Uses three `Conv1D` blocks with filter counts [64, 128, 128].
- `BatchNormalization` is used to stabilize training.

### GRU Layers (Temporal)
- Captures the "rhythm" and duration of human movements.
- Two GRU layers with units [64, 32].
- `Dropout` (0.3) is applied to prevent overfitting.

---

## 📈 Data Augmentation

To handle class imbalance (especially "Fall" events), we use three types of synthetic augmentation:
1.  **Gaussian Noise**: Adding 2% jitter to simulate real-world interference.
2.  **Magnitude Scaling**: ±10% amplitude variation to simulate distance changes.
3.  **Time Shifting**: ±50ms temporal shifts to handle rhythmic variations.

---

## 🎯 Fall Detection Logic

The system implements multi-stage fall detection:

### 1. Confidence Thresholding
- Fall probability threshold: **65%** per window
- Requires **3 consecutive windows** of high fall confidence to trigger alert
- Prevents false positives from transient signal anomalies

### 2. Exponential Moving Average (EMA) Smoothing
- Alpha coefficient: **0.4** for temporal smoothing
- Debounces prediction jitter and stabilizes classification

### 3. Alert Triggering
- When fall conditions are met, the system:
  1. Logs to CSV for post-analysis
  2. Sends POST request to `alert_python_backend`
  3. Backend dispatches Firebase Cloud Messaging (FCM) notification
  4. Mobile app receives alert and displays emergency UI

---

## 🛠️ Performance & Scalability

- **Accuracy**: Current model achieves **87.2%** accuracy on the test set.
- **Latency**: Sub-millisecond inference time on the host machine.
- **Portability**: The system is designed to run on any host with a Python environment and Serial connection to the ESP32.
- **Quantization**: TensorFlow Lite quantized models available for edge deployment.

---

## 📊 System Configuration

Key configuration parameters in `fall_detector_logic/config/settings.py`:

| Parameter | Default Value | Purpose |
|-----------|---------------|---------|
| `SERIAL_PORT` | `COM3` | ESP32 RX node connection |
| `BAUD_RATE` | `921600` | High-speed serial communication |
| `SUBCARRIERS` | `114` | HT40 Wi-Fi subcarrier count |
| `WINDOW_SIZE` | `50` | CSI packets per window (500ms @ 100Hz) |
| `HOP_SIZE` | `25` | Overlap ratio (50%) |
| `RSSI_FLOOR` | `-85` | Noise rejection threshold (dBm) |
| `FALL_PROBABILITY_THRESHOLD` | `0.65` | Fall alert confidence |
| `CONSECUTIVE_DETECTIONS` | `3` | Windows for debouncing |

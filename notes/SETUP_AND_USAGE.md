# Setup and Usage: Wi-Fi CSI Fall Detection System

Follow these steps to set up the hardware and software for real-time fall detection using Wi-Fi Channel State Information.

## 🔌 Hardware Setup

### 1. Requirements
- 2x ESP32 Development Boards (e.g., NodeMCU, DevKitV1).
- 1x Host PC (Laptop/Desktop) for inference and data collection.

### 2. Flashing Firmware
- Use the source code in `fall_detector_logic/firmware/`.
- **TX Node**: Flash `tx_node/` to one ESP32. This node will broadcast UDP packets at 100Hz.
- **RX Node**: Flash `rx_node/` to the other ESP32. This node captures CSI and sends it via Serial (COM3 @ 921600 baud).

### 3. Physical Placement
- Place the TX and RX nodes 2–3 meters apart.
- Ensure a clear Line-of-Sight (LoS) for baseline measurements.
- The system detects disturbances in the Wi-Fi field between the nodes.

---

## 💻 Software Environment

### 1. Prerequisites
- Python 3.9 - 3.11 (TensorFlow 2.15 compatibility).
- Visual Studio Code (recommended).
- A Virtual Environment to run the project (recommended).

### 2. Installation
Navigate to `fall_detector_logic/` and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Audit `fall_detector_logic/config/settings.py` for:
- `SERIAL_PORT`: Ensure it matches your RX node's COM port.
- `BAUD_RATE`: Must be `921600` for high-speed data.

---

## 🚀 Usage Guide

### 1. Data Collection
To record new activity samples:
```bash
cd fall_detector_logic
python scripts/collect_data.py --class walk --samples 10
```
This will record 10-second samples for the specified activity.

### 2. Training
Train the CNN-GRU hybrid model:
```bash
python scripts/train_model.py
```
Check `models/` directory for saved model files and scalar parameters.

### 3. Real-time Inference
Launch the live inference system:
```bash
python runners/inference_runner.py
```
Ensure the RX node is connected and the COM port is correct.

### 4. Alert Backend
To enable fall detection alerts, set up the Python alert backend:
```bash
cd alert_python_backend
pip install -r requirements.txt
python alert_sender.py
```
Ensure Firebase service account credentials are configured in `serviceAccountKey.json`.

---

## ⚠️ Troubleshooting
- **COM Port Error**: Check Device Manager and update `settings.py`.
- **Low Accuracy**: Ensure the environment is static during "empty" class recording.
- **OOM Errors**: Reduce the augmentation limit in `settings.py`.

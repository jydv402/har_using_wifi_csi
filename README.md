# Wi-Fi CSI Human Activity Recognition (HAR) System

A robust, real-time Human Activity Recognition system leveraging Wi-Fi Channel State Information (CSI) from ESP32 devices. This project uses a hybrid CNN-GRU deep learning model to detect and classify activities such as walking, sitting, falling, and more.

## 🌟 Core Features

- **Real-time Sensing**: 100Hz CSI packet rate for high-fidelity movement tracking.
- **Deep Learning Architecture**: Hybrid 1D-CNN (Spatial) + GRU (Temporal) model.
- **Fall Detection**: Specialized logic and training for critical safety events (Fall Detection).
- **Data Pipeline**: End-to-end pipeline from ESP32 raw CSI to processed training windows.
- **Inference Dashboard**: Real-time visualization of activity probabilities and signal trends.

## 🏗️ System Architecture

1.  **Sensing Layer**: ESP32 TX node broadcasts UDP packets; ESP32 RX node captures CSI and forwards to host via Serial.
2.  **Processing Layer**: Python-based pipeline for Z-score normalization, outlier removal, and windowing.
3.  **Intelligence Layer**: TensorFlow/Keras model running in real-time on the host (Laptop/Edge).

## 📂 Project Structure

- `project_v2/`: Main development directory.
  - `src/`: Source code for data processing and models.
  - `config/`: Centralized system settings.
  - `firmware/`: ESP-IDF source for TX and RX nodes.
  - `models/`: Trained model files and scalers.
- `notes/`: Detailed technical guides and setup instructions.

## 🚀 Getting Started

Please refer to the detailed guides in the `notes/` directory:
- [Setup and Usage](file:///d:/Projects/major/notes/SETUP_AND_USAGE.md)
- [Technical Guide](file:///d:/Projects/major/notes/TECHNICAL_GUIDE.md)

---
*Developed as part of the Major Project for Wi-Fi Sensing.*

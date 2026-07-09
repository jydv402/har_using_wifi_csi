# Wi-Fi CSI Fall Detection System

A comprehensive, real-time fall detection and human activity recognition system leveraging Wi-Fi Channel State Information (CSI) from ESP32 devices. This project integrates wireless sensing, deep learning inference, and mobile alerting to provide an intelligent safety monitoring solution.

## 📋 Project Overview

This project implements an end-to-end fall detection pipeline that combines:
- **CSI-based Sensing**: Real-time Wi-Fi Channel State Information capture from ESP32 devices at 100Hz packet rate
- **Advanced Deep Learning**: Hybrid 1D-CNN (spatial features) + GRU (temporal features) architecture for accurate activity classification
- **Fall Detection Logic**: Specialized algorithms to detect and alert on fall events
- **Python Backend**: Real-time data processing, model inference, and firebase-based alerting
- **Flutter Mobile App**: User-friendly interface for monitoring and receiving alerts

## 🌟 Core Features

- **Real-time Sensing**: 100Hz CSI packet rate for high-fidelity movement tracking
- **Deep Learning Architecture**: Hybrid CNN-GRU model for accurate activity classification (walking, sitting, falling, etc.)
- **Specialized Fall Detection**: Dedicated logic and training for critical safety events
- **End-to-End Data Pipeline**: From ESP32 raw CSI to processed training windows with normalization and outlier removal
- **Alert System**: Firebase-based notifications for detected fall events
- **Mobile App**: Cross-platform Flutter application for real-time monitoring
- **Multi-Node Support**: Distributed TX/RX ESP32 nodes with routing capabilities

## 📂 Project Structure

### **`fall_detector_logic/`** - Core Detection & Training Engine
Main directory for fall detection algorithms and deep learning models.
- **`src/`**: Core Python source code
  - `data/`: Data processing and loading utilities
  - `models/`: Neural network architecture definitions
  - `utils/`: Helper functions for preprocessing and inference
- **`config/`**: Centralized system configuration
  - `settings.py`: Configuration parameters and hyperparameters
- **`models/`**: Pre-trained model files
- **`firmware/`**: ESP32 firmware source code
  - `tx_node/`: Transmitter node firmware (broadcasts Wi-Fi packets)
  - `rx_node/`: Receiver node firmware (captures CSI data)
- **`data/`**: Training and test datasets
- **`scripts/`**: Utility and automation scripts
- **`runners/`**: Execution pipelines for model training and inference

### **`alert_python_backend/`** - Alert & Notification Service
Backend service for processing fall detection events and sending notifications.
- **`alert_sender.py`**: Main alert dispatching logic using Firebase Cloud Messaging
- **`requirements.txt`**: Python dependencies for the backend service
- **`serviceAccountKey.json`**: Firebase authentication credentials
- **`tokens.txt`**: Device tokens for FCM push notifications

### **`fall_alert/`** - Flutter Mobile Application
Cross-platform mobile app for real-time monitoring and alert reception.
- **`lib/`**: Flutter application source code
- **`android/`**: Android-specific configuration and build files
- **`ios/`**: iOS-specific configuration and build files
- **`web/`**: Web deployment files
- **`windows/`** / **`linux/`** / **`macos/`**: Additional platform support
- **`pubspec.yaml`**: Flutter package dependencies and configuration

### **`notes/`** - Documentation & Guides
Comprehensive technical documentation and setup instructions.
- **`SETUP_AND_USAGE.md`**: Step-by-step setup, installation, and usage guide
- **`TECHNICAL_GUIDE.md`**: Detailed technical architecture and implementation details
- **`GLOSSARY.md`**: Key terminology and acronyms used in the project
- **`FLOW_DIAGRAM.md`**: Visual system flow and data pipeline diagrams
- **`alert_flow.md`**: Fall detection and alert flow documentation
- **`fall_detector_logic/`**: Additional logic documentation

### **Root Level Files**
- **`requirements.txt`**: Main Python dependencies
- **`open_venv.ps1`**: PowerShell script to activate Python virtual environment
- **`.gitignore`**: Git exclusion rules

## 🏗️ System Architecture

The project follows a three-layer architecture:

1. **Sensing Layer**: ESP32 TX/RX nodes for CSI capture at 100Hz
   - TX Node: Broadcasts Wi-Fi beacon frames
   - RX Node: Captures CSI data and forwards via Serial/UART

2. **Processing Layer**: Python pipeline for real-time data processing
   - Z-score normalization for feature scaling
   - Outlier detection and removal
   - Sliding window generation for model input
   - CSI routing and aggregation

3. **Intelligence Layer**: Deep learning inference and decision making
   - TensorFlow/Keras model for activity classification
   - Fall detection logic with confidence thresholding
   - Firebase backend for alert distribution
   - Mobile app for user notification and monitoring

## 🚀 Getting Started

1. **Setup**: Refer to [`notes/SETUP_AND_USAGE.md`](notes/SETUP_AND_USAGE.md) for complete installation and configuration instructions.

2. **Understanding the System**: Read [`notes/TECHNICAL_GUIDE.md`](notes/TECHNICAL_GUIDE.md) for detailed architecture and implementation details.

3. **System Flow**: Check [`notes/FLOW_DIAGRAM.md`](notes/FLOW_DIAGRAM.md) for data pipeline visualization.

4. **Terminology**: Consult [`notes/GLOSSARY.md`](notes/GLOSSARY.md) for key terms and acronyms.

## 📊 Key Technologies

- **Hardware**: ESP32 microcontroller units with Wi-Fi capability
- **Backend**: Python 3.x, TensorFlow/Keras
- **Frontend**: Flutter (cross-platform mobile)
- **Cloud**: Firebase (Cloud Messaging, Database)
- **Data Processing**: NumPy, Pandas, Scikit-learn
- **Deployment**: TensorFlow Lite for edge inference

## 📝 License & Attribution

*Developed as part of the Major Project for Wi-Fi-based Sensing and Human Activity Recognition.*

---

**For detailed information on any component, refer to the documentation in the `notes/` directory.**

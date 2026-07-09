# 📚 Project Glossary: Technical Terms Explained

This glossary provides simple, educational explanations for the technical terms used throughout the Wi-Fi CSI Fall Detection project.

---

## 📡 Wireless & Hardware Terms

### **CSI (Channel State Information)**
- **What it is**: A digital "fingerprint" of the Wi-Fi signal.
- **Why we use it**: Standard Wi-Fi signals (RSSI) only tell you how strong a signal is. CSI tells you how the signal bounced off walls, furniture, and **people**. It is sensitive enough to detect heartbeats or the specific motion of a fall.
- **In our code**: Handled by `fall_detector_logic/firmware/rx_node` and parsed in `fall_detector_logic/src/data/parser.py`.

### **RSSI (Received Signal Strength Indicator)**
- **What it is**: The raw "loudness" of the Wi-Fi signal.
- **Why we use it**: We use it as a simple filter. If the RSSI is too low (the signal is too quiet), the CSI data is likely just static noise and should be ignored.
- **In our code**: Filtered in `fall_detector_logic/src/data/parser.py` using the `RSSI_FLOOR` from `fall_detector_logic/config/settings.py`.

### **HT40 (High Throughput 40MHz)**
- **What it is**: A Wi-Fi mode that uses a wider frequency band (40MHz instead of 20MHz).
- **Why we use it**: It provides 114 subcarriers (data points) instead of 52. More subcarriers mean higher resolution and better accuracy for the AI model.

---

## 🧠 Machine Learning & AI Terms

### **CNN (Convolutional Neural Network)**
- **What it is**: An AI architecture originally designed for images. It "slides" a filter over data to find local patterns.
- **Why we use it**: In our project, we treat the 114 subcarriers like a 1D image. The CNN looks for "spatial" patterns across the frequencies (e.g., "Are the high frequencies moving differently than the low ones?").
- **In our code**: Defined in `fall_detector_logic/src/models/`.

### **GRU (Gated Recurrent Unit)**
- **What it is**: A type of "Recurrent" neural network that has memory. It processes data in order.
- **Why we use it**: Human activity is a sequence. A "Fall" isn't a single moment; it's a sequence of "Standing -> Moving Fast -> On Floor". The GRU remembers the past few milliseconds to understand the motion.
- **In our code**: Defined in `fall_detector_logic/src/models/`.

### **Softmax**
- **What it is**: A mathematical function used at the very end of a model.
- **Why we use it**: It turns the model's complex math scores into **probabilities** that add up to 100%. For example: `[Walk: 0.1, Fall: 0.85, Empty: 0.05]`.
- **In our code**: Used in the final layer of `src/models/cnn_gru.py`.

### **Focal Loss**
- **What it is**: A "penalty" system that punishes the model more for missing hard classes (like Falls) and less for easy classes (like Empty Room).
- **Why we use it**: We don't have many "Fall" recordings compared to "Empty" recordings. Focal Loss stops the model from getting "lazy" and only predicting "Empty".

---

## 🧪 Data Processing (DSP)

### **Median Filter**
- **What it is**: A cleaning technique that looks at a window of data and replaces the center point with the "middle" value.
- **Why we use it**: It removes sudden "spikes" or "sparkles" in the signal (Impulse Noise) without blurring the edges of a real movement.
- **In our code**: Implemented in `fall_detector_logic/src/data/preprocessor.py`.

### **Z-Score Normalization (Standardization)**
- **What it is**: Shifting and scaling data so the average is 0 and the spread is 1.
- **Why we use it**: Neural networks learn much faster when all input numbers are in the same small range.
- **In our code**: Handled by the `StandardScaler` in `fall_detector_logic/src/data/preprocessor.py`.

### **Data Augmentation**
- **What it is**: Creating "fake" but realistic variations of your data.
- **Why we use it**: We add a tiny bit of noise or shift the timing of a "Fall" slightly left or right. This forces the model to learn the *concept* of a fall rather than just memorizing a specific file.
- **In our code**: Implemented in `fall_detector_logic/src/data/loader.py`.

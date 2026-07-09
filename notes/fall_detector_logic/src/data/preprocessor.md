# Textbook:## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: Used for basic array management and outlier clipping.
- **`scipy.signal` (`medfilt`)**: Implements the technical **Median Filter**.
    - **Usage**: Removes sudden static spikes from the Wi-Fi signal without blurring the edges of real movement.
- **`sklearn.preprocessing` (`StandardScaler`)**: A machine learning utility for data scaling.
    - **Usage**: Ensures every Wi-Fi subcarrier has a mean of 0 and variance of 1, preventing high-energy signals from drowning out subtle motions.
- **`joblib`**: A tool for saving and loading Python objects.
    - **Usage**: Saves the trained `StandardScaler` to disk so the live [inference dashboard](file:///d:/Projects/major/notes/fall_detector_logic/scripts/inference_dashboard.md) can use the exact same settings as the training phase.
- **`os`**: Standard Python library for file path management.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Central configuration file.
    - **Usage**: Retrieves the `DENOISE_KERNEL` size to determine how aggressively to clean the data.

## 📖 Overview
CSI data is inherently noisy. The `src/data/preprocessor.py` acts as a "Digital Car Wash," cleaning and polishing the radio signal before it enters the neural network.

---

## 💻 Code Walkthrough

### 1. Denoising (Median Filter)
```python
18:     def remove_outliers(self, csi_matrix):
25:         for i in range(csi_matrix.shape[1]):
26:             filtered[:, i] = medfilt(csi_matrix[:, i], kernel_size=settings.DENOISE_KERNEL)
```
-   **Line 18-26**: Applies a **Median Filter** along the time-axis of each individual subcarrier. This is highly effective at removing "Impulse Noise" (single spikes) while preserving the edges of real human movement patterns. Unlike a "Mean Filter" (average), the median isn't pulled away by extreme outliers.

### 2. Normalization (Z-Score)
```python
15:         self.scaler = StandardScaler()
32:         flat_data = csi_matrix.reshape(-1, csi_matrix.shape[-1])
33:         self.scaler.fit(flat_data)
```
-   **Lines 15-33**: Uses Scikit-learn's `StandardScaler`. This subtracts the *mean* and divides by the *standard deviation*. 
-   **Why?**: Deep Learning models (especially RNNs/GRUs) perform poorly if inputs have wildly different scales (e.g., Subcarrier A is at 10 and Subcarrier B is at 500). Normalization centered around zero (with a variance of 1) speeds up training significantly.

### 3. Window Generation
```python
54:         num_windows = (len(csi_matrix) - window_size) // hop_size + 1
58:         windows = np.array([
59:             csi_matrix[i * hop_size : i * hop_size + window_size]
60:             for i in range(num_windows)
61:         ])
```
-   **Line 54**: The "Sliding Window" formula. It calculates how many overlapping blocks can fit into the continuous data stream.
-   **Example**: If you have 100 packets, a `window_size` of 50, and a `hop_size` of 10, you get 6 windows. This "Data Reuse" dramatically increases the number of training samples available to the model.

### 4. Data Augmentation (Synthetic Variation)
```python
81:     def augment_noise(self, csi_window, noise_std=0.05):
83:         noise = np.random.normal(0, noise_std, csi_window.shape)
84:         return csi_window + noise
```
-   **Lines 81-84**: **Gaussian Noise Injection**. By adding tiny random numbers to real data, we force the model to look for the "Shape" of the movement rather than the exact "Values" of the subcarriers. This prevents **Overfitting** (where the model memorizes your specific room layout).

---

---

## 🎓 Concept Deep-Dives

### 1. What is a Median Filter?
Imagine a sequence of Wi-Fi readings: `[10, 11, 999, 10, 12]`. That `999` is a clear noise spike (maybe a microwave interfered).
- **Mean Filter (Average)**: Would give you `~208`. The noise ruined the whole window.
- **Median Filter**: Sorts them (`[10, 10, 11, 12, 999]`) and picks the middle: **11**.
- **Result**: The noise is deleted completely, and the real signal signal (`10`, `11`, `12`) is perfectly preserved.
- **Reference**: See [GLOSSARY.md](file:///d:/Projects/major/notes/GLOSSARY.md#median-filter) for more.

### 2. Standardization (Z-Score)
Wi-Fi hardware doesn't have a volume knob. One subcarrier might have a "strength" of 500, while another is at 10.
- **The Problem**: If you feed these directly into a model, the model will think the "500" carrier is 50x more important than the "10" carrier, which is false!
- **The Solution**: Standardization (Line 32) rescales every subcarrier to have an average of **0** and a spread of **1**. Now the model can compare them fairly.

---

## 🔗 Related Notes & Dependencies
- **Configuration**: The `DENOISE_KERNEL` size is defined in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).
- **Application**: This logic is used during training in [loader.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md) and during live testing in [inference_dashboard.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/inference_dashboard.md).

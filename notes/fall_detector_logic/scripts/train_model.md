# Textbook:## 📦 Library Reference

### External Libraries
- **`sklearn.model_selection` (`StratifiedKFold`)**: A statistical reliability tool.
    - **Usage**: Splits the data into "folds" to ensure the model is tested on every single recording at least once.
- **`pandas` (as `pd`)**: Fast CSV reading and data manipulation.
- **`numpy` (as `np`)**: Bulk matrix handling for large datasets.

### Local Dependencies
- **[src.data.preprocessor](file:///d:/Projects/major/notes/fall_detector_logic/src/data/preprocessor.md)**: Scales and cleans the raw recordings.
- **[src.models.cnn_gru](file:///d:/Projects/major/notes/fall_detector_logic/src/models/cnn_gru.md)**: Defines the actual shape of the "Brain" (CNN and GRU layers).
- **[src.models.trainer](file:///d:/Projects/major/notes/fall_detector_logic/src/models/trainer.md)**: The helper class that actually runs the training loop.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides hyperparameter values like `LEARNING_RATE` and `EPOCHS`.

## 📖 Overview
The `train_model.py` is the "Training Simulator." It takes all the CSV data you collected, passes it through the hybrid network, and optimizes the weights until the system can accurately tell the difference between a "Fall" and a "Walk."
 It is designed to be highly transparent, showing every step from data loading to TFLite optimization.

---

## 💻 Code Walkthrough

### 1. Unified Data Loading
```python
37:             df_peek = pd.read_csv(file_path, nrows=1)
38:             if 'subcarrier_0' in df_peek.columns:
40:                 df = pd.read_csv(file_path)
41:                 csi_matrix = df.drop(columns=['timestamp', 'rssi'], errors='ignore').values.astype(np.float32)
42:             else:
44:                 df = pd.read_csv(file_path, header=None)
45:                 csi_matrix = df.values.astype(np.float32)
```
-   **Line 37-45**: **Auto-Format Detection**. The project has two types of CSVs (Amplitudes-only and Raw-with-metadata). This logic looks for the string "subcarrier_0" to decide how to parse the file. This flexibility allows the user to mix and match collection methods.

### 2. Window Construction
```python
48:             windows = preprocessor.create_overlapping_windows(
49:                 csi_matrix, 
50:                 window_size=settings.WINDOW_SIZE, 
51:                 hop_size=settings.HOP_SIZE
52:             )
```
-   **Line 48-52**: Deep Learning models for time-series (like GRU) cannot process an entire 10-second file at once. We break it into small "windows" (e.g., 50 packets). The `hop_size` determines how much overlap exists between windows.

### 3. Data Augmentation
```python
90:     print("Applying Data Augmentation...")
94:         augmented = preproc.augment_window(X_clean[i])
95:         X_aug_list.append(np.expand_dims(augmented, axis=0))
```
-   **Line 90-95**: To make the model more robust, we create "mutated" versions of the real data. For example, adding tiny amounts of random noise. This effectively doubles the size of our dataset and prevents "overfitting".

### 4. Cross-Validation
```python
105:     kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
111:     for train_idx, val_idx in kfold.split(X_clean, y):
117:         model = build_cnn_gru_model(input_shape, num_classes)
118:         trainer = ModelTrainer(model)
```
-   **Line 105-111**: **K-Fold**. The data is split into 5 pieces. We train on 4 and test on 1, repeating this 5 times. This gives us a statistically honest score of how the model will perform in the real world on data it hasn't seen before.

### 5. Deployment (TFLite)
```python
134:     tflite_path = os.path.join(settings.MODEL_DIR, 'har_model_quantized.tflite')
135:     trainer.export_tflite(X_train, tflite_path)
```
-   **Line 134-135**: Converts the heavy Keras model into a lightweight "FlatBuffer" format (`.tflite`). This step often includes **Quantization**, which shrinks the model size by converting 32-bit floating point numbers into 8-bit integers, making it run faster on mobile devices.

---

---

## 🎓 Concept Deep-Dives

### 1. What is K-Fold Cross-Validation?
If you test your model on the same data you used for training, it's like a student memorizing the answers to a test. They didn't "Learn"; they just "Cheated."
- **K-Fold (Line 95)**: Splits your data into 5 pieces (Folds). It trains on 4 and tests on 1. Then it rotates and repeats 5 times.
- **The Benefit**: It ensures that your model works on *all* your data samples, not just a lucky few. It provides a "Review Score" you can actually trust.

### 2. Deep Dive: Data Augmentation
CSI data can change if a person wears a different jacket or moves an inch to the left.
- **Noise Injection**: We add 2% random static. This forces the model to ignore background noise.
- **Time Shifting**: We slide the window slightly. This ensures the model recognizes a "Fall" regardless of whether it started at the beginning or end of the 0.5s window.
- **Result**: A model that isn't afraid of a messy signal!

---

## 🔗 Related Notes & Dependencies
- **The Pipeline**: This script uses the [loader.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md) to gather and balance the training samples.
- **Architecture**: It compiles the hybrid network defined in [cnn_gru.md](file:///d:/Projects/major/notes/fall_detector_logic/src/models/cnn_gru.md).
- **Automation**: Training metrics and best-model saving are handled by the [trainer.md](file:///d:/Projects/major/notes/fall_detector_logic/src/models/trainer.md).

---

## 🎯 Key Takeaways
-   **End-to-End**: A single script handle from data ingest to deployment-ready artifacts.
-   **Validation**: Stratified splitting ensures that each fold has a representative mix of all activities.
-   **Efficiency**: Using overlapped windows allows us to extract hundreds of training samples from a single 10-second recording.

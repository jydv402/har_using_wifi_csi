# Textbook: `src/data/loader.py`

## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: Used for final array stacking and type casting (`float32`).
- **`pandas` (as `pd`)**: Used for high-speed CSV reading and label mapping.
- **`pathlib` (`Path`)**: Modern replacement for `os.path`. Makes handling file systems easier.
- **`os`**: Included for directory creation and environment checks.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides activity class names and subcarrier counts.
- **[src.data.preprocessor](file:///d:/Projects/major/notes/fall_detector_logic/src/data/preprocessor.md)**: The sister module used to scale and window the data.
    - **Usage**: The loader passes raw data through the `CSIPreprocessor` before returning it to the model.

## 📖 Overview
The `UniversalDataLoader` is the "Logistics Manager" of the project. It visits every folder in the dataset, cleans the files, balances the amounts of "Fall" vs "Walk" data, and serves it on a platter to the AI trainer. Its job is to find all the CSV files from different activity folders, balance the dataset so no activity is under-represented, and package everything into an ultra-fast binary format (`.npz`) for the model trainer.

---

## 💻 Code Walkthrough

### 1. Data Ingestion
```python
87:         for cls in self.classes:
88:             cls_dir = self.data_dir / cls
91:             csv_files = list(cls_dir.glob("*.csv"))
106:                     df = pd.read_csv(file_path, header=header_val)
110:                         csi_data = df.iloc[:, 2:settings.SUBCARRIERS+2].values
```
-   **Lines 87-91**: Iterates through folders named after activities (`walk`, `fall`, etc.).
-   **Line 110**: Uses Pandas `iloc` (Integer-Location-based indexing) to slice the relevant subcarrier columns out of the raw spreadsheets.

### 2. Minority Class Augmentation
```python
29:         target_per_class = min(np.max(counts), settings.AUG_MAX_SAMPLES_PER_CLASS)
38:                 needed = target_per_class - count
45:                 augment_indices = np.random.choice(cls_indices, size=needed, replace=True)
```
-   **Line 29**: Identifies the "Majority Class" (the activity with the most samples). 
-   **Line 38-45**: If a class like "Fall" has fewer samples, this script uses **Oversampling**. It picks random existing "Fall" samples and applies the transformations from `preprocessor.py` (noise, scaling, shifting) to create unique synthetic variations until the classes are balanced.

### 3. Caching System
```python
76:         cache_path = settings.PROCESSED_DATA_DIR / "har_dataset_cache.npz"
78:         if use_cache and cache_path.exists():
80:             data = np.load(cache_path)
81:             return data['X'], data['y']
166:         np.savez_compressed(cache_path, X=X, y=y)
```
-   **Lines 76-81**: Processing thousands of CSV files can take minutes. To save time, the loader saves the final "Ready-to-Train" NumPy arrays into a **Compressed NPZ** file.
-   **Line 166**: On the second run, the loader skips everything and loads the binary data in milliseconds.

### 4. Global Normalization
```python
153:             self.preprocessor.fit_scaler(X_flat)
154:             X_normalized = self.preprocessor.transform(X_flat)
161:             self.preprocessor.save(scaler_path)
```
-   **Lines 153-161**: Calculates the training dataset's overall Mean and Standard Deviation. Crucially, it saves these values to `scaler.pkl`. Any model trained with this loader *must* use this `scaler.pkl` to understand incoming signals correctly.

---

---

## 🎓 Concept Deep-Dives

### 1. What is Data Balancing?
Imagine trying to teach a child to identify fruits, but you show them 1,000 apples and only 1 orange. The child will likely guess "Apple" for everything.
- **In our project**: We have thousands of seconds of "Empty Room" data but maybe only 10 seconds of "Fall" data.
- **The Solution (Line 38)**: We use **Oversampling**. The loader identifies the "Minority Class" (Falls) and creates synthetic copies of those samples until they match the count of the "Majority Class". This ensures the AI doesn't become biased.

### 2. Why use binary caching (.npz)?
Reading 5,000 individual CSV files from a hard drive is slow because it involves "Disk I/O overhead."
- **The Problem**: Training takes 10 minutes, but 8 of those minutes are spent just reading files.
- **The Solution (Line 166)**: We package everything into a single, compressed binary file (`.npz`). This format is native to NumPy, allowing the computer to "slurp" the entire dataset into RAM in seconds.

---

## 🔗 Related Notes & Dependencies
- **Preprocessing**: This loader uses the `CSIPreprocessor` defined in [preprocessor.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/preprocessor.md) to clean the data.
- **Configuration**: The folder locations and class names are defined in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).
- **Consumer**: The output of this loader is fed into the [trainer.md](file:///d:/Projects/major/notes/fall_detector_logic/src/models/trainer.md).

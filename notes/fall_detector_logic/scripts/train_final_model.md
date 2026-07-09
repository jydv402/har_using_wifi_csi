# Textbook:## 📦 Library Reference

### External Libraries
- **`sklearn.model_selection` (`train_test_split`)**: Used to reserve a final percentage of data for the "Grand Prize" verification.
- **`tensorflow` & `numpy`**: Standard ML engines.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Governs final model filenames and paths.
- **[src.data.loader](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md)**: Aggregates all collected data into one giant training pile.
- **[src.models.cnn_gru](file:///d:/Projects/major/notes/fall_detector_logic/src/models/cnn_gru.md)**: Constructs the final "Brain" architecture.
- **[src.models.trainer](file:///d:/Projects/major/notes/fall_detector_logic/src/models/trainer.md)**: Manages the final, high-epoch training run.

## 📖 Overview
Once you have finished collecting all your data, `train_final_model.py` is the script you run to create the "Golden Copy" of your system. This model is the one you will eventually deploy to the [Inference Dashboard](file:///d:/Projects/major/notes/fall_detector_logic/scripts/inference_dashboard.md).
---

## 💻 Code Walkthrough

### 1. Abstracted Data Loading
```python
17:     loader = UniversalDataLoader()
18:     X, y = loader.load_dataset(normalize=settings.NORMALIZE)
```
-   **Line 17-18**: Instead of manually searching folders and parsing CSVs, it calls the `UniversalDataLoader`. This makes the script much cleaner and ensures that any data-loading bugs fixed in the central `src/data/loader.py` are automatically applied here.

### 2. Standardized Splitting
```python
25:     X_train, X_val, y_train, y_val = train_test_split(
26:         X, y, test_size=0.2, random_state=42, stratify=y
27:     )
```
-   **Line 25-27**: Performed a standard 80/20 split. Using `stratify=y` is critical to ensure that the 20% validation set correctly represents all activities (especially rare events like "Falls").

### 3. Model Training and Summary
```python
36:     model = build_cnn_gru_model(input_shape, num_classes)
37:     model.summary()
41:     history = trainer.train(X_train, y_train, X_val, y_val)
```
-   **Line 37**: Prints a table of all the layers (CNN filters, GRU units, Dense layers). This is the final "sanity check" to ensure the architecture matches the design specifications.
-   **Line 41**: Executes the training loop. This produces the `history` object which tracks loss and accuracy over time (Epochs).

### 4. Final Artifact Export
```python
45:     final_model_path = settings.MODEL_DIR / "final_har_model.keras"
46:     model.save(final_model_path)
```
-   **Line 45-46**: Saves the final model in the modern `.keras` format (which is a single-file ZIP encompassing weights and metadata). This file is what the `InferenceDashboard` will load for real-time predictions.

---

## 🎯 Key Takeaways
-   **Simplicity**: Production scripts should be "Thin". They shouldn't contain complex logic; instead, they should just orchestrate calls to the `src` package.
-   **Auditability**: By printing the `model.summary()` and the dataset shapes, developers can audit the training run logs to ensure everything was correct.
-   **The "Gold" Model**: This script produces the one "Final" model that represents the culmination of all collected data.

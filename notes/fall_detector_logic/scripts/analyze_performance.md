# Textbook: `scripts/analyze_performance.py`

## 📦 Library Reference

### External Libraries
- **`sklearn.metrics` (`confusion_matrix`, `classification_report`)**: The "Judge" of the model.
    - **Usage**: Calculates exactly how many mistakes the model made and why (Precision, Recall, F1).
- **`sklearn.model_selection` (`train_test_split`)**: Splits the data into a "Final Exam" (testing set) that the model has never seen before.
- **`tensorflow` (as `tf`)**: Loads the trained model file (`.h5` or `.tflite`) for evaluation.
- **`numpy` & `pandas`**: Used for data loading and matrix math.

### Local Dependencies
- **[src.data.loader](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md)**: Retrieves the entire dataset for evaluation.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides the activity labels for the confusion matrix axis.

## 📖 Overview
The `analyze_performance.py` is the "Final Exam" for your AI. It takes your finished model and a slice of your best data to generate a detailed report card showing its accuracy, errors, and areas for improvement.rained Human Activity Recognition (HAR) model. It performs the following key functions:
1.  Loads the processed dataset.
2.  Analyzes the distribution of activity classes (to check for imbalance).
3.  Loads a pre-trained Keras model (`.h5` format).
4.  Runs predictions on a validation set and generates a detailed classification report and confusion matrix.

---

## 💻 Code Walkthrough

### 1. Imports and environment setup
```python
1: import os
2: import sys
3: import numpy as np
4: import tensorflow as tf
5: from pathlib import Path
6: from sklearn.model_selection import train_test_split
7: from sklearn.metrics import confusion_matrix, classification_report
8: import pandas as pd
10: # Ensure project root is in PYTHONPATH
11: sys.path.append(str(Path(__file__).parent.parent))
```
-   **Lines 1-8**: Standard data science and machine learning imports. `tensorflow` is used for model handling, while `sklearn` provides the metrics and data splitting utilities.
-   **Lines 10-11**: Crucial for local development. This adds the project root to the Python search path, allowing the script to import `config` and `src` regardless of where it is launched from.

### 2. Loading the Dataset
```python
16: def analyze_model_performance():
17:     # 1. Load Data
18:     loader = UniversalDataLoader()
19:     X, y = loader.load_dataset(normalize=settings.NORMALIZE)
```
-   **Line 18-19**: Initializes the `UniversalDataLoader` and calls `load_dataset`. The `normalize` parameter ensures the data is in the same scale as it was during training (Z-score normalized).

### 3. Class Distribution Analysis
```python
25:     # 2. Check Distribution
26:     print("\n--- Class Distribution ---")
27:     class_counts = {}
28:     for i, cls in enumerate(settings.CLASSES):
29:         count = np.sum(y == i)
30:         class_counts[cls] = count
31:         print(f"{cls:<10}: {count} samples ({count/len(y):.1%})")
```
-   **Lines 28-31**: Iterates through the classes defined in `settings.py`. It counts how many samples exist for each class (e.g., how many "walk" windows vs "fall" windows). Understanding this is vital because if one class is significantly under-sampled, the model might struggle to learn it.

### 4. Model Loading and Data Splitting
```python
34:     model_path = settings.MODEL_DIR / "final_har_model.h5"
35:     if not model_path.exists():
36:         print(f"Model not found at {model_path}")
37:         return
38:         
39:     print(f"\nLoading model: {model_path}")
40:     model = tf.keras.models.load_model(model_path, compile=False)
41:     
42:     # Stratified Split (same as training)
43:     X_train, X_val, y_train, y_val = train_test_split(
44:         X, y, test_size=0.2, random_state=42, stratify=y
45:     )
```
-   **Line 40**: Loads the model using `tf.keras.models.load_model`. `compile=False` is used because we only want to run inference (predicting), not continue training, which avoids needing to re-specify the optimizer or loss function.
-   **Line 43-45**: Splits the data into 80% training (ignored here) and 20% validation. The `stratify=y` argument ensures that both the training and validation sets have the same proportion of each activity class.

### 5. Prediction and Metrics
```python
47:     print("\nRunning validation predictions...")
48:     y_pred_probs = model.predict(X_val, verbose=1)
49:     y_pred = np.argmax(y_pred_probs, axis=1)
51:     # 4. Metrics
52:     print("\n--- Classification Report ---")
53:     present_classes = [settings.CLASSES[i] for i in np.unique(y_val)]
54:     print(classification_report(y_val, y_pred, target_names=present_classes))
```
-   **Line 48**: The model outputs a probability distribution for each window (e.g., "[0.1, 0.8, 0.1]" for a 3-class model).
-   **Line 49**: `np.argmax` picks the index with the highest probability (in this example, index 1).
-   **Line 54**: `classification_report` calculates Precision, Recall, and F1-score. This tells us exactly which activities the model is "confused" about.

### 6. Confusion Matrix
```python
56:     print("\n--- Confusion Matrix ---")
57:     cm = confusion_matrix(y_val, y_pred)
58:     cm_df = pd.DataFrame(cm, index=present_classes, columns=present_classes)
59:     print(cm_df)
```
-   **Lines 57-59**: Generates a confusion matrix. The rows represent the *actual* activity, and the columns represent the *predicted* activity. This allows you to see, for instance, if "walk" is being incorrectly predicted as "run".

---

## 🎓 Concept Deep-Dives

### 1. What is a Confusion Matrix?
It is a "Mistake Map." Imagine a grid where the Rows are "What actually happened" and the Columns are "What the AI guessed."
- **The Goal**: A perfect model has a bright diagonal line (where Actual = Guessed).
- **The Insight**: If you see a cluster in the "Fall" row but "Sit" column, you know the room layout or movement speed is confusing the model between those two activities.

### 2. Understanding Precision vs. Recall (F1-Score)
Accuracy (90%) can be lying to you.
- **Recall**: "If a person falls, did the system catch them?" (Crucial for safety).
- **Precision**: "If the system alerted, was it actually a fall?" (Crucial to avoid annoying neighbors).
- **F1-Score (Line 54)**: This is the harmonic mean of both. It's the most honest "Grade" for a model because it punishes models that are only good at one and bad at the other.

---

## 🔗 Related Notes & Dependencies
- **Model Target**: Analyzes the performance of the architecture defined in [cnn_gru.md](file:///d:/Projects/major/notes/fall_detector_logic/src/models/cnn_gru.md).
- **Training Source**: Metrics are derived from the cross-validation performed in [train_model.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/train_model.md).
- **Labels**: Reads the activity names from [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

---

## 🎯 Key Takeaways
-   **Stratification**: Always use stratified splits when evaluating performance to ensure fair representation of all activities.
-   **Probability Output**: The model doesn't just say "Walk"; it gives a probability. `np.argmax` converts that confidence into a hard prediction.
-   **Diagnostics**: If the F1-score for "Fall" is low, you know you need to collect more fall data or adjust the model architecture.

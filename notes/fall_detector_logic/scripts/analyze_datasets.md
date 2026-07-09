# 📄 scripts/analyze_datasets.py

## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: Used for statistical profiling.
    - **Usage**: Calculates the **Standard Deviation** and **Average Amplitude** of the raw signal packets.
- **`pandas` (as `pd`)**: The high-speed data reader.
    - **Usage**: Used to quickly ingest raw CSV files to extract a sample for analysis.
- **`pathlib` (`Path`)**: Used for robust file system navigation across different folders.
- **`os` & `sys`**: Standard libraries used for project path integration.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Defines the `RAW_DATA_DIR` and the list of activity labels to search for.

## 📖 Overview
The `analyze_datasets.py` is the "Lab Technician" of the project. Before you spend hours training a model, you should run this script to ensure your data is actually healthy. It performs a high-speed "Physical Exam" on every folder in your dataset to find common problems like silent sensors or mixed-up samples.

---

## 🎓 Concept Deep-Dives

### 1. Diagnostic Insights (Anomaly Detection)
The script doesn't just show numbers; it looks for patterns that indicate a hardware problem.
- **Near-Zero Check**: If the "Empty" mean is too low, your hardware might have been disconnected or muted during recording.
- **Class Contrast (Lines 71-75)**: This is a crucial metric. If a "Fall" looks exactly like "Empty" (same variance), the AI will never be able to tell them apart, no matter how many hours you train it.

---

## 💻 Code Walkthrough

### 1. Sampling Strategy (Line 36)
Instead of reading 100% of your data (which could be gigabytes), the script takes a representive "Biopsy":
```python
36:         for f in files[:15]: # Take a good sample size
```

### 2. Contrast Ratio (Lines 72-73)
```python
72:         ratio = fall_profile['std'] / (empty_profile['std'] + 1e-6)
73:         print(f"✅ Class Contrast (Fall vs Empty Variance): {ratio:.2f}x")
```
This ratio tells you how much "Louder" a fall is compared to the background noise. A ratio > 1.5 is healthy.

---

## 🎯 Key Takeaways
-   **dataset Health**: Run this immediately after a recording session to make sure your data was saved correctly.
-   **Troubleshooting**: If your model accuracy is low, check this script. The problem is usually that the "Contrast" is too low (e.g., the sensor was placed too far away from the activity).
-   **Fast Feedback**: Provides a high-level summary of your total sample counts across all classes.

---

## 🔗 Related Notes & Dependencies
- **Data Source**: Checks folders created by [collect_data.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/collect_data.md) or [collect_raw_csv.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/collect_raw_csv.md).
- **Next Step**: Once data contrast is verified, proceed to [train_model.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/train_model.md).

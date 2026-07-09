# 📄 scripts/analyze_patterns.py

## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: The primary statistical engine.
    - **Usage**: Calculates the **Temporal Variance** (`np.var`) and **Mean Amplitude** (`np.mean`) across samples.
- **`pandas` (as `pd`)**: Used for data organization and comparison.
    - **Usage**: Aggregates the statistics for all classes into a single table (DataFrame) for easy side-by-side comparison.
- **`matplotlib.pyplot` (as `plt`)**: The visualization engine.
    - **Usage**: Generates a bar chart showing movement intensity per activity type.
- **`pathlib` (`Path`)**: Modern file system manager for project-wide paths.
- **`os`**: Standard library used for creating the `evaluation/` output directory.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides the official list of activity `CLASSES`.
- **[src.data.loader](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md)**: The data bridge that fetches the raw recordings for analysis.

## 📖 Overview
The `analyze_patterns.py` is a "Signal Telescope." While other scripts focus on the whole system, this one zooms in on the individual activities to see how they "Look" mathematically. It specifically looks for:
1.  **Motion Intensity**: Using variance to see how much the radio waves "Wiggle" when someone is moving vs. standing still.
2.  **Relative Disturbance**: Calculates an "Activity Index" to compare how distinct one activity is from another.

---

## 🎓 Concept Deep-Dives

### 1. What is Temporal Variance? (Motion Intensity)
In Wi-Fi sensing, a static room has a steady signal. When a human moves, the signal jumps up and down.
- **Variance**: Measures how much the signal deviates from its average.
- **The Insight**: A "Fall" or "Run" will have very high variance because the body is moving rapidly through many subcarriers. "Empty" should have near-zero variance.

---

## 💻 Code Walkthrough

### 1. Stats Calculation (Lines 35-46)
The script iterates through every activity class, finds all samples belonging to that class, and calculates their statistical "Fingerprint."
```python
37:         # Calculate temporal variance (indicator of motion)
38:         sample_var = np.var(cls_data, axis=1) # (Samples, Subcarriers)
39:         mean_var = np.mean(sample_var)
```

### 2. Activity Index (Lines 44-46)
```python
46:         activity_index = mean_var / (mean_amp + 1e-6)
```
This index helps normalize the data—if a signal is naturally weak, a tiny wiggle might look like a huge fall. The index adjusts for the baseline strength.

---

## 🎯 Key Takeaways
-   **Class Contrast**: Use this script to verify that your activities are actually distinct. If "Fall" and "Walk" have the same variance, your AI will likely confuse them.
-   **Output**: The script saves a visual comparison to `evaluation/class_variance_patterns.png` for use in technical presentations.
-   **Validation**: This is a great "Pre-Training" check. If "Empty" has high variance, your environment is too noisy!

---

## 🔗 Related Notes & Dependencies
- **Data Source**: Analyzes recordings gathered by the [collect_data.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/collect_data.md).
- **Evaluation**: Complements the model-level reports in [analyze_performance.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/analyze_performance.md).

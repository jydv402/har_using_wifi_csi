# Textbook: `src/data/migrator.py`

## 📦 Library Reference

### External Libraries
- **`pandas` (as `pd`)**: Used for reading foreign CSV formats (like WiFall's specific structure).
- **`numpy` (as `np`)**: Used for frequency manipulation and bulk data saving.
- **`glob`**: Used to find every file in a dataset by searching for patterns (e.g., `*.csv`).
- **`os`, `sys`, `pathlib`**: Used for directory navigation and project-wide path management.

### Local Dependencies
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: The core engine of the migrator.
    - **Usage**: Uses `CSIParser.interpolate_csi` to force external data into our project's 114-subcarrier standard.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Defines where the new harmonized data should be saved.

## 📖 Overview
Public datasets are recorded differently. The `DataMigrator` is a "Foreign Exchange Office"—it takes CSI data from other researchers and converts it into the exact "Currency" (format) our model needs. Researchers around the world have public datasets like **ESP-Fi** and **WiFall**. However, these datasets use different formats (e.g., 52 subcarriers instead of 114). The `DataMigrator` harmonizes these into our project's standardized CSV format.

---

## 💻 Code Walkthrough

### 1. Activity Mapping
```python
28:         self.esp_fi_activity_map = {
29:             "1": "run",
30:             "2": "fall",
31:             "3": "walk",
...
36:         }
```
-   **Lines 28-36**: Different datasets use different numeric codes or names for activities. This mapping dictionary translates external IDs into our project's standard labels (`run`, `fall`, `walk`, etc.). This ensures that regardless of the source, our model sees a consistent set of classes.

### 2. Mocking the CSI stream
```python
89:                 # Mock line: CSI_DATA,id,mac,rssi,rate,...[data]
90:                 mock_line = f"CSI_DATA,0,00:00:00:00:00:00,{rssi},0,0,0,0,0,0,0,0,0,0,{data_str}"
92:                 parsed = self.parser.parse_line(mock_line)
```
-   **Lines 89-92**: Instead of writing a whole new parser for every dataset, we "trick" our existing `CSIParser`. We wrap the raw data string from the public dataset into a fake serial line (`CSI_DATA...`) and pass it to the parser.
-   **Benefit**: This reuse ensures that the way we interpolate subcarriers for external data is *identical* to how we handle live data, maintaining mathematical consistency.

### 3. Harmonization (Interpolation)
```python
19:     # Uses CSIParser for subcarrier interpolation (52 -> 114).
```
-   **Line 19**: Most public datasets (like ESP-Fi) were recorded using 20MHz Wi-Fi (52 subcarriers). Our model expects 114 subcarriers (40MHz). The migrator uses the `interp1d` logic hidden in `parser.py` to "up-sample" the data smoothly, effectively making the old data look like it was recorded on our modern 40MHz setup.

---

---

## 🎓 Concept Deep-Dives

### 1. What is "Domain Shift"?
If you train a model on your room and then test it in a different room, the performance usually drops. This is **Domain Shift**.
- **In this project**: Public datasets like ESP-Fi were recorded in different environments and with different antennas.
- **The Fix (Line 92)**: By using our `CSIParser` to re-process external data, we perform **Data Harmonization**. We force the external "foreign" data to look identical to our own data format, making our model more "Universal."

### 2. Why use Reference Datasets?
Machine learning is data-hungry. Collecting 10,000 "Falls" in your own house would be painful (and dangerous!).
- **Goal**: We use the migrator to ingest thousands of already-recorded events from global researchers. This provides the "Big Data" foundation that makes our model robust against different body types and movement speeds.

---

## 🔗 Related Notes & Dependencies
- **Core Tool**: This script acts as a wrapper around the [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md).
- **Storage**: Processed data is saved into the directory defined in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).
- **Training**: The output of this migrator is consumed by the [loader.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md) for final training.

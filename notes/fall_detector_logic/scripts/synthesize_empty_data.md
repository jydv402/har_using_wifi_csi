# Textbook: `scripts/synthesize_empty_data.py`

## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: The random noise generator.
    - **Usage**: Uses `np.random.normal` to create "Standard Deviation" noise that mimics the natural static of an empty room.
- **`pandas` (as `pd`)**: Used to read the template files and save the millions of newly generated synthetic samples to CSV.
- **`pathlib` (`Path`)**: Handles directory creation for the new datasets.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Tells the script where to save the synthetic logs.

## 📖 Overview
An AI needs "Silence" (EMPTY data) just as much as it needs "Action." The `synthesize_empty_data.py` is a data factory that takes a small "DNA Sample" of a quiet room and creates thousands of fake recordings to help balance your dataset.
 `synthesize_empty_data.py` solves this by **Augmenting Reality**. It takes a few real "Empty" recordings and uses their statistical properties (mean and standard deviation) to generate hundreds of synthetic CSV files that look like real Wi-Fi noise.

---

## 💻 Code Walkthrough

### 1. Template Loading
```python
12: def load_template_csi(file_path):
14:     df = pd.read_csv(file_path)
19:             df = pd.read_csv(file_path, header=None)
24:         return df.iloc[:, 2:settings.SUBCARRIERS+2].values.astype(np.float32)
```
-   **Line 12-21**: This function is a "Smart Loader". It tries to see if the CSV has a header or not. 
-   **Line 24**: It extracts just the amplitude columns (skipping the timestamp and RSSI) so they can be analyzed for noise patterns.

### 2. Statistical Profiling
```python
37:     baselines = []
38:     noise_stds = []
40:     if template_files:
41:         for tf in template_files:
42:             csi = load_template_csi(tf)
44:                 baselines.append(np.mean(csi, axis=0))
45:                 noise_stds.append(np.std(csi))
```
-   **Line 44**: Calculates the **Baseline** (average signal level) for every subcarrier in the real recording.
-   **Line 45**: Calculates the **Standard Deviation** (how much the signal "wiggles" naturally). Each room has a unique noise floor depending on environmental interference.

### 3. Data Generation
```python
54:     for i in range(num_samples):
56:         idx = np.random.randint(0, len(baselines))
61:         jittered_baseline = baseline * np.random.uniform(0.95, 1.05, size=baseline.shape)
64:         noise = np.random.normal(0, noise_std, size=(packets_per_sample, settings.SUBCARRIERS))
65:         sample_data = jittered_baseline + noise
```
-   **Line 61**: **Baseline Jitter**. We don't want every synthetic file to be identical. We multiply the baseline by a random factor between 0.95 and 1.05. This simulates the signal being slightly stronger or weaker (e.g., if a door was opened elsewhere in the house).
-   **Line 64**: **Gaussian Noise**. Generates a matrix of random numbers based on the captured `noise_std`. 
-   **Line 65**: Combines the jittered baseline and the new noise to create a "fake" CSI recording that is mathematically indistinguishable from a real empty room to the GRU model.

---

---

## 🎓 Concept Deep-Dives

### 1. Why Sythesize "Empty" Data?
An AI is only as smart as the data it sees. If you only show it people falling, it might think the "Empty Room" is just a very slow fall.
- **The Challenge**: Recording a room for 5 hours just for "Empty" data is boring and wastes disk space.
- **The Solution (Line 38)**: We take a small sample of *real* empty data, calculate its "Pulse" (mean and std), and then use math to generate thousands of "Fake" minutes that sound exactly like the real thing. This teaches the model the "Baseline Silence" of your room.

---

## 🔗 Related Notes & Dependencies
- **Data Source**: Analyzes templates processed by the [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md).
- **Loader Integration**: The resulting synthetic CSVs are read by the [loader.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md) as a separate class.
- **Configuration**: Uses the `EMPTY` class name from [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

---

## 🎯 Key Takeaways
-   **Data Balancing**: In Machine Learning, if you have 1000 "Walk" samples but only 10 "Empty" samples, the model will assume a person is always walking. Synthesizing data ensures your "EMPTY" class is just as strong as your active classes.
-   **Domain Randomization**: By varying the baseline (Jitter), the model learns that "Empty" isn't a single fixed value, but a *range* of stable values.
-   **Reproducibility**: Generating data with `np.random.normal` ensures that our "Empty" class captures the generic behavior of Gaussian noise found in radio signals.

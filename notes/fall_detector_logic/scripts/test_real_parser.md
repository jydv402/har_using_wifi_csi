# 📄 scripts/test_real_parser.py

## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: Used for the mathematical verification of the HT-LTF signal.
- **`pathlib` (`Path`)**: Handles the relative imports from the project core.

### Local Dependencies
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: The core engine under specific scrutiny.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Defines the project's subcarrier standard.

## 📖 Overview
The `test_real_parser.py` is a "Forensics Script." It uses a **real-world payload** captured from actual ESP32 logs. This is different from a simulated test because it uses messy, real data with the exact noise and encoding used by the Espressif hardware.

---

## 💻 Code Walkthrough

### 1. Real Payload (Line 16)
The script uses a massive 384-value string (192 IQ pairs) taken from a real `log_RX.txt` file.
```python
16:     real_line = 'CSI_DATA,615140,1a:00:00:00:00:00,-72,11,1,0,1,1,1,0,0,0,0...
```

### 2. Mathematics Verification (Lines 38-39)
This check confirms that the parser is calculating the "Amplitude" correctly from the raw I and Q parts:
```python
38:         # i= -28, q= 13 -> amp = sqrt(28^2 + 13^2) = sqrt(784+169) = 30.87
39:         print(f"   Probe (First HT-LTF Amp): {parsed['amplitudes'][0]:.2f} (Expected ~30-31)")
```

---

## 🎯 Key Takeaways
-   **Hardware Alignment**: Confirms that our Python math matches the ESP32's signal logic.
-   **Extraction Logic**: Verifies that the parser successfully skips the "LLTF" (Legacy) part of the packet and finds the high-quality "HT-LTF" (High Throughput) data required for the project.

---

## 🔗 Related Notes & Dependencies
- **Technical Deep-Dive**: See [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md) for the full explanation of the I/Q to Amplitude conversion math.

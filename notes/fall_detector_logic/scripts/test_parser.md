# 📄 scripts/test_parser.py

## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: Used to calculate the mathematical mean of the simulated signal data.
- **`pathlib` (`Path`)**: Ensures the test script can find the project's internal files.

### Local Dependencies
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: The code being tested.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides the expected `SUBCARRIER` count for verification.

## 📖 Overview
The `test_parser.py` is a "Diagnostic Lab." Its job is to simulate perfect Wi-Fi packets and see if the parser correctly extracts the information. This is used to ensure that the code handles both modern "Key-Value" formats and legacy "Bracketed" formats.

---

## 💻 Code Walkthrough

### 1. Simulated Packet (Line 16)
The script creates a "Fake" serial line that looks exactly like what an ESP32 would send.
```python
16:     test_line = "CSI_DATA,RSSI,-65,SNR,15,LEN,256,DATA," + ",".join(["1"] * 256)
```

### 2. Validation (Lines 21-32)
It then checks if the parser was able to:
1.  Read the RSSI (-65).
2.  Count the subcarriers (256).
3.  Extract actual data (non-zero test).

---

## 🎯 Key Takeaways
-   **Stability**: If you modify the `CSIParser` code to support a new hardware model, run this script first. If this script fails, you broke the baseline compatibility.
-   **Legacy Support**: Specifically verifies that the parser hasn't "Forgotten" how to read older, bracketed data formats.

---

## 🔗 Related Notes & Dependencies
- **Core Engine**: Tests the logic inside [parser.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md).
- **Pro-Tip**: Use this as a template if you ever need to add support for a new Wi-Fi payload format.

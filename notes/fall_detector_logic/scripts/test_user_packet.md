# 📄 scripts/test_user_packet.py

## 📦 Library Reference

### External Libraries
- **`numpy` (as `np`)**: Calculates the mean and spread of the user's specific Wi-Fi data.
- **`pathlib` (`Path`)**: Correctly maps the project structure to find the parser.

### Local Dependencies
- **[src.data.parser](file:///d:/Projects/major/notes/fall_detector_logic/src/data/parser.md)**: The component being validated against external user data.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Used to verify that the packet length matches the project's global configuration.

## 📖 Overview
The `test_user_packet.py` script is a "Verification Receipt." It was designed to debug a specific data format provided by a project contributor. It ensures that the parser can handle longer metadata strings (timestamps, MAC addresses) without losing the actual CSI signal at the end of the line.

---

## 💻 Code Walkthrough

### 1. The "Problem" Packet (Line 15)
The user provided a packet where the timestamp was very long (`2092610`). The test verifies that our parser doesn't get "Confused" by the extra digits.
```python
15:     user_line = 'CSI_DATA,615329,1a:00:00:00:00:00,-72,11,1,0,1,1,1,0,0,0,0...
```

### 2. Double-Check Verification (Lines 36-44)
The script manually performs the same checks the "Textbook" user would:
1.  **RSSI Check**: Did we get exactly `-72`?
2.  **Length Check**: Did we get exactly `settings.SUBCARRIERS`?

---

## 🎯 Key Takeaways
-   **Robustness**: This script proves the parser can handle variations in metadata length.
-   **Debugging Tool**: If you find a packet in your logs that causes an error, you should copy it into a script like this to isolate and fix the bug.

---

## 🔗 Related Notes & Dependencies
- **Diagnostic Partner**: Use this alongside [test_parser.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/test_parser.md) for full coverage.

# Textbook: `scripts/test_alert_logic.py`

## 📦 Library Reference

### External Libraries
- **`unittest.mock` (`MagicMock`, `patch`)**: The core of the testing suite.
    - **Usage**: `patch` "kidnaps" real functions (like the serial reader) and replaces them with a harmless robot (the Mock) that does whatever the test tells it to.
- **`numpy` (as `np`)**: Used to generate fake signal windows.

### Local Dependencies
- **[scripts.inference_dashboard](file:///d:/Projects/major/notes/fall_detector_logic/scripts/inference_dashboard.md)**: The logic being tested.
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Provides the thresholds for checking if the alert logic works as intended.

## 📖 Overview
Safety software must work every time. The `test_alert_logic.py` is a "Security Drill"—it tricks the dashboard into thinking a fall occurred just to make sure the alerting and logging code responds correctly without needing a real human to fall.
It "fakes" (mocks) the ML model and the serial port, feeding the `InferenceDashboard` specific mathematical scenarios to see if it responds correctly.

---

## 💻 Code Walkthrough

### 1. Mocking the Environment
```python
18:     with patch('tensorflow.keras.models.load_model') as mock_load, \
19:          patch('scripts.inference_dashboard.AsyncSerialReader') as mock_serial:
22:         mock_model = MagicMock()
24:         mock_load.return_value = mock_model
27:         dashboard = InferenceDashboard("COM_MOCK", "models/final_har_model.keras")
```
-   **Line 18-19**: Using `unittest.mock.patch`, the script disables the real TensorFlow and Serial libraries. This allows the test to run in milliseconds and work on computers that don't have a GPU or an ESP32 plugged in.
-   **Line 22-27**: Creates a "Mock Model" and tells the dashboard to use it. Now, we have a fully functional dashboard that won't try to open real files.

### 2. Simulating a Fall
```python
42:         probs = np.zeros(len(dashboard.classes))
43:         probs[fall_idx] = 0.70  # Above 0.65 threshold
48:         for i in range(settings.CONSECUTIVE_DETECTIONS):
49:             dashboard._handle_alerts(probs)
```
-   **Line 42-43**: Defines a probability vector where "Fall" is 70%.
-   **Line 48-49**: Calls the alert handler multiple times. This tests the **Sequential Logic**. If `CONSECUTIVE_DETECTIONS` is set to 3, the alert shouldn't fire on the 1st or 2nd call, but it *must* fire on the 3rd.

### 3. Verifying the Journal
```python
58:         print("\n2. Testing Fall Journaling")
59:         log_file = Path("logs/fall_history.csv")
76:             if after_size > before_size:
77:                 print(f"✅ Fall logged to {log_file}")
```
-   **Line 58-77**: Checks if the system correctly wrote to the CSV log. It compares the file size before and after the simulated alert. If the size increased, the test passes.

---

---

## 🎓 Concept Deep-Dives

### 1. What is Mocking?
Testing the "Fall Detection Alert" is hard because you don't want to actually fall on the floor 50 times just to check if a text message was sent.
- **Mocking (Line 25)**: We create a "Fake" model. We tell it: "Pretend you just saw a Fall with 95% confidence." 
- **The Benefit**: We can test the *logic* of the alert (Does it sound the alarm only after 3 falls? Does it wait 5 seconds between logs?) without ever turning on the Wi-Fi or moving a muscle.

---

## 🔗 Related Notes & Dependencies
- **Logic Under Test**: Verifies the alert heuristics found in the [inference_dashboard.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/inference_dashboard.md).
- **Configuration**: Uses the `ALERT_THRESHOLD` and `MIN_CONSECUTIVE_FALLS` from [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).
---

## 🎯 Key Takeaways
-   **Decoupling**: Mocking allows you to test the *logic* of your application separately from its *dependencies* (TensorFlow, Serial).
-   **Boundary Testing**: You can use this script to test edge cases. What happens if the probability is exactly 0.65? What happens if it's 0.64? 
-   **Automation**: This script can be run automatically every time the code is changed to ensure a "refactor" didn't accidentally break the fall detection alerts.

# Textbook: `firmware/tx_node` (CSI Transmitter)

## 📦 Library Reference (ESP-IDF)

### External Components
- **`esp_wifi`**: Controls the Wi-Fi radio.
    - **Usage**: Sets the radio to a fixed channel (e.g., Channel 11) to avoid interference.
- **`esp_now`**: The communication engine.
    - **Usage**: Sends "Magic Packets" to the RX node at exactly 100 times per second.
- **`esp_mac`**: Handles the unique identity for the hardware.

### Local Dependencies
- **[rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md)**: The TX node's silent partner.

## 📖 Overview
The `tx_node` is the "Light Bulb" of the project. It doesn't listen—it only shines. It broadcasts high-speed Wi-Fi pulses constantly, acting as the light source that the `rx_node` uses to "See" shadows and movement in the environment. Its consistency is what allows the Receiver to detect the small "wobbles" in the signal caused by human movement.

---

## 💻 Code Walkthrough: `app_main.c`

### 1. ESP-NOW Protocol
```c
120:     esp_now_rate_config_t rate_config = {
121:         .phymode = CONFIG_ESP_NOW_PHYMODE,
122:         .rate = CONFIG_ESP_NOW_RATE,
```
-   **Line 120-122**: Instead of standard Wi-Fi (which requires a password and connection time), we use **ESP-NOW**. This is a low-latency protocol that sends raw packets directly between chips. 
-   **PHY Mode**: We set it to `HT40` and `MCS0`. This ensures that every "Hello!" pulse is exactly the same width and frequency, which is crucial for a clean baseline.

### 2. The Broadcast Loop
```c
150:     esp_now_peer_info_t peer = {
154:         .peer_addr = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff},
155:     };
```
-   **Line 150-155**: The transmitter target address is set to `0xff:ff:ff:ff:ff:ff`. This is a **Broadcast** address. It means the TX node doesn't care who is listening; it just throws the signal into the air for any RX node to catch.

### 3. Precision Timing
```c
162:     for (uint32_t count = 0; ; ++count) {
163:         esp_err_t ret = esp_now_send(peer.peer_addr, (const uint8_t *)&count, sizeof(count));
168:         usleep(1000 * 1000 / CONFIG_SEND_FREQUENCY);
169:     }
```
-   **Line 162-163**: It sends a simple counter (0, 1, 2, 3...). This helps the Receiver know if it missed any packets (e.g., if the Receiver sees `count=5` then `count=7`, it knows it missed packet #6).
-   **Line 168**: This is the "Heartbeat" pacing. `1000 * 1000 / 100` equals 10,000 microseconds (10 milliseconds). This ensures a perfect **100Hz** signal rate.

---

---

## 🎓 Concept Deep-Dives

### 1. What is ESP-NOW?
Traditional Wi-Fi is like a phone call—you have to dial, wait for a connection, and stay "on the line."
- **ESP-NOW**: Is like a **Walkie-Talkie**. You just press a button and shout. 
- **The Benefit (Line 154)**: Because there is no "handshake" or connection delay, we can transmit a packet every 10 milliseconds perfectly, which is required for high-frequency motion detection.

### 2. Understanding PHY Rates (MCS)
**MCS (Modulation and Coding Scheme)** defines how the data is encoded in the radio waves.
- **Our Setting (Line 40)**: `WIFI_PHY_RATE_MCS0_LGI`.
- **The Why**: MCS0 is the most "Basic" and "Robust" mode. It wraps the data in a very thick layer of protection, making the signal harder to lose. Since our objective is to measure the *environment*, we want a signal that is as stable and simple as possible.

---

## 🔗 Related Notes & Dependencies
- **The Listener**: This beacon's signal is caught and analyzed by the [rx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/rx_node.md).
- **Timing**: The `CONFIG_SEND_FREQUENCY` (Line 41) MUST match the `CSI_PACKET_RATE` in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

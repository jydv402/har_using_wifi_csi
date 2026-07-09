# Textbook: `firmware/rx_node` (CSI## 📦 Library Reference (ESP-IDF)

### External Components
- **`esp_wifi`**: The fundamental wireless driver.
    - **Usage**: Puts the radio into "CSI Secret Mode" and configures the antenna for 40MHz bandwidth.
- **`esp_now`**: A peer-to-peer messaging protocol.
    - **Usage**: Used to coordinate with the TX node and extract raw packet metadata.
- **`esp_csi_gain_ctrl`**: ESP-IDF component for hardware signal gain.
    - **Usage**: Crucial for ensuring the signal doesn't get "Clipped" when someone walks too close to the sensor.
- **`nvs_flash`**: Non-Volatile Storage.
    - **Usage**: Stores Wi-Fi credentials and node MAC addresses so the device remembers them after a power cut.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Referenced in spirit (hardware constants must match).

## 📖 Overview
The `rx_node` is the "Satellite Dish" of the project. It sits quietly and listens for radio pulses from the `tx_node`, using custom Espressif drivers to peel back the "Data" layer of the Wi-Fi packet and reveal the raw CSI signal hidden inside.
 calculates the "Channel State Information" (CSI)—a fingerprint of how the radio waves were bounced and twisted by the environment.

---

## 💻 Code Walkthrough: `app_main.c`

### 1. Wi-Fi Configuration
```c
93:     ESP_ERROR_CHECK(esp_wifi_set_bandwidth(ESP_IF_WIFI_STA, CONFIG_WIFI_BANDWIDTH));
119:     ESP_ERROR_CHECK(esp_wifi_set_mac(WIFI_IF_STA, CONFIG_CSI_SEND_MAC));
```
-   **Line 93**: Forces the Wi-Fi card into **HT40 (40MHz)** mode. This provides higher frequency resolution (more subcarriers) than standard 20MHz Wi-Fi.
-   **Line 119**: Sets a **Static MAC Address**. This ensures the Receiver only listens to OUR Transmitter and ignores other neighbors' Wi-Fi traffic.

### 2. The CSI Callback (The Heart)
```c
137: static void wifi_csi_rx_cb(void *ctx, wifi_csi_info_t *info)
```
-   **Line 137**: This function is triggered by the hardware every single time a packet arrives (100 times per second). It provides a raw buffer containing the I and Q values for every subcarrier.

### 3. Serial Communication (The Funnel)
```c
177:     ets_printf("CSI_DATA,%d," MACSTR ",%d,%d,%d,%d,%d,%d,%d,%d,%d",
203:     ets_printf(",%d,%d,\"[%d", info->len, info->first_word_invalid, (int16_t)(info->buf[0]));
```
-   **Lines 177-203**: The ESP32 converts the binary data into a long, comma-separated string starting with `CSI_DATA`.
-   **High Performance**: We use `ets_printf` (a low-level, fast print function) instead of the standard `printf` to ensure we can keep up with the 100Hz packet rate without causing buffer overflows.

### 4. Hardware Filtering
```c
250:     wifi_csi_config_t csi_config = {
251:         .lltf_en           = true,
252:         .htltf_en          = true,
...
255:         .channel_filter_en = true,
258:     };
```
-   **Lines 250-258**: This tells the hardware *exactly* what type of Wi-Fi pulses to measure. We enable `htltf_en` (High Throughput Long Training Field) to get the detailed 40MHz CSI data.

---

---

## 🎓 Concept Deep-Dives

### 1. How does the ESP32 see CSI?
Wi-Fi hardware has a component called the "Equalizer." Its job is to undo the distortions caused by walls.
- **The Magic**: To do this, the hardware calculates a complex number for every "Subcarrier" (frequency). By exposing this hidden data to Python, we can "see" through walls using the distortions as a sensor.
- **Reference**: See [GLOSSARY.md](file:///d:/Projects/major/notes/GLOSSARY.md#csi-channel-state-information) for more.

### 2. What are Training Fields (LLTF/HT-LTF)?
Wi-Fi packets start with a "Header" that contains a known musical tone (A "Training Field").
- **Goal**: Because the Receiver knows *exactly* what this tone is supposed to sound like, it can compare it to what it *actually* heard. The difference between the two is the CSI.
- **Configuration (Line 251)**: Enabling `lltf_en` and `htltf_en` tells the ESP32 to start this comparison math.

---

## 🔗 Related Notes & Dependencies
- **Communication**: The output of this firmware is captured by the [serial_utils.md](file:///d:/Projects/major/notes/fall_detector_logic/src/utils/serial_utils.md).
- **The Beacon**: This node depends on signals sent by the [tx_node.md](file:///d:/Projects/major/notes/fall_detector_logic/firmware/tx_node.md).
- **Configuration**: Packet rates and channels must match the settings in [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

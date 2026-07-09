# Textbook: `src/models/cnn_gru.py`
## 📦 Library Reference

### External Libraries
- **`tensorflow` (as `tf`)**: The primary deep learning framework.
    - **Usage**: Provides the `Sequential` model container and all layers (`Conv1D`, `GRU`, `Dense`). It also handles the hardware-level optimization for GPU execution.
- **`keras` layers**:
    - **Usage**: `Conv1D` for frequency patterns, `MaxPooling1D` for downsampling, `GRU` for time-memory, and `Dropout` to prevent the model from over-training.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Defines the network architecture specifics.
    - **Usage**: Pulls `settings.CNN_FILTERS` and `settings.GRU_UNITS` to scale the model size dynamically.

## 📖 Overview
The `src/models/cnn_gru.py` defines the "Brain" of the Wi-Fi CSI Fall Detection system. It uses a **Hybrid Architecture**—Convolutional layers for spatial clarity and Gated Recurrent Units for temporal memory—to understand the story behind radio wave distortions caused by human activity, particularly detecting falls.
1.  **CNN (Convolutional Neural Network)**: Acts as the "Eyes". It looks at the 114 subcarriers and extracts frequency-spatial patterns (e.g., "Are the high frequencies moving more than the low frequencies?").
2.  **GRU (Gated Recurrent Unit)**: Acts as the "Memory". It looks at how the CNN features change over time (e.g., "The frequencies spiked, then stabilized—that's a fall!").

---

## 💻 Code Walkthrough: `build_cnn_gru_model`

### 1. The CNN Layers (Spatial Filtering)
```python
17:     model.add(Conv1D(filters=settings.CNN_FILTERS[0], 
18:                      kernel_size=settings.CNN_KERNEL_SIZE, 
19:                      activation='relu', 
20:                      padding='same'))
22:     model.add(MaxPooling1D(pool_size=2))
```
-   **Line 17-20**: The `Conv1D` layer slides a filter across the subcarriers. By using 64 filters, it can simultaneously search for 64 different types of signal "shapes" (like a sudden dip in the 3rd subcarrier).
-   **Line 22**: `MaxPooling1D` reduces the data size by half, keeping only the strongest signals. This makes the model "Translation Invariant" (meaning it works even if the person moves slightly to the left or right).

### 2. The GRU Layers (Temporal Sequence)
```python
41:     model.add(GRU(units=settings.GRU_UNITS[0], return_sequences=True))
42:     model.add(Dropout(settings.DROPOUT_RATE))
44:     model.add(GRU(units=settings.GRU_UNITS[1], return_sequences=False))
```
-   **Line 41**: The first GRU layer processes the sequence and passes its "Hidden State" to the next layer (`return_sequences=True`).
-   **Line 44**: The second GRU layer summarizes the entire 50-packet window into a single representative vector (`return_sequences=False`). 
-   **Line 42-45**: **Dropout**. This randomly "turns off" 30-50% of the neurons during training. This forces the model to be robust and prevents it from over-relying on a single noisy subcarrier.

### 3. The Classification Head
```python
52:     model.add(Dense(num_classes, activation='softmax', name="activity_output"))
```
-   **Line 52**: The final **Softmax** layer converts the internal numbers into **Probabilities**. It ensures that if you add up the probabilities for "Walk", "Fall", and "Empty", they always equal 1.0 (100%).

---

## 💻 Code Walkthrough: `focal_loss_custom`

### 1. Handling Imbalance
```python
68: def focal_loss_custom(num_classes, gamma=2.0, alpha=0.25):
83:         weight = alpha * tf.math.pow(1.0 - y_pred, gamma)
84:         loss = weight * cross_entropy
```
-   **Lines 68-84**: Standard Cross-Entropy loss treats every mistake the same. **Focal Loss** is different. It "down-weights" easy examples (like "Empty Room") and focuses the model's energy on hard examples (like "Fall"). If the model is 90% sure it's "Empty", the `1.0 - y_pred` term becomes very small, so the model stops obsessing over that sample and spends more time learning what a "Fall" looks like.

---

---

## 🎓 Concept Deep-Dives

### 1. What is a CNN and why use it for Wi-Fi?
A **Convolutional Neural Network (CNN)** is typically used for images. Imagine sliding a magnifying glass over a photo to find edges and shapes.
- **In this project**: We treat our 114 subcarriers like a 1D strip of pixels.
- **Goal**: The CNN layers find "spatial" relationships across frequencies. For example, a heavy person moving might affect lower frequencies differently than a lighter person. The CNN identifies these "Spectral Shapes."
- **Reference**: See [GLOSSARY.md](file:///d:/Projects/major/notes/GLOSSARY.md#cnn-convolutional-neural-network) for more.

### 2. What is a GRU and why use it for HAR?
A **Gated Recurrent Unit (GRU)** is a "Memory Cell." Unlike standard neurons that forget everything immediately, a GRU looks at a data point and decides whether to "remember" it or "reset" its memory.
- **In this project**: Human activity is a **Time Series**. A "Fall" is defined by what happened 100ms ago vs now.
- **Goal**: The GRU captures the **Temporal Dynamics** (the rhythm of movement). It turns the static snapshots from the CNN into a "Story" of action.

### 3. What is Softmax?
Sitting at the very end of our model (Line 52), **Softmax** is like a "Judge" that makes the final call.
- **The Problem**: Internal layers produce large raw numbers (e.g., `[12.5, -3.2, 5.1]`).
- **The Solution**: Softmax squashes these numbers into a range of 0 to 1, ensuring they all add up to 100%. This gives us a clear **Confidence Score** for each activity.

### 4. Focal Loss vs. Standard Loss
Usually, AI models use "Cross-Entropy" loss. However, in our system, "Empty Room" data is much more common than "Fall" data.
- **The Risk**: A standard model might decide to *always* guess "Empty" because it's right 90% of the time, even if it misses every fall.
- **The Fix**: **Focal Loss** (implemented on Line 68) adds a "weight" that makes mistakes on rare classes (Falls) much more "painful" for the model, forcing it to focus on learning the hard classes.

---

## 🔗 Related Notes & Dependencies
- **Data Source**: This model is trained using data packaged by [loader.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md).
- **Configuration**: Layer counts and units are pulled from [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).
- **Inference**: This model is executed in real-time by the [inference_dashboard.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/inference_dashboard.md).

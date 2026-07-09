# Textbook: `src/models/trainer.py`

## 📦 Library Reference

### External Libraries
- **`tensorflow` (as `tf`)**: Orchestrates the training process.
    - **Usage**: Compiles the model with the optimizer, handles data shuffling during training, and executes the mathematical back-propagation.
- **`sklearn.utils` (`class_weight`)**: A utility to fix "Unfair" datasets.
    - **Usage**: Automatically calculates how much more "importance" to give to the rare "Fall" class so the AI doesn't ignore it.
- **`os`**: Standard library used to save the finished model file to the hard drive.

### Local Dependencies
- **[config.settings](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md)**: Sets the training boundaries.
    - **Usage**: Retrieves `settings.EPOCHS` (how long to train) and `settings.LEARNING_RATE`.

## 📖 Overview
Training an AI is like teaching a student. `ModelTrainer` acts as the "Teacher," showing the model millions of examples and correcting its mistakes using **Gradient Descent** and specialized **Loss Functions**. Its job is to:
1.  **Optimize Hardware**: Detect and use GPUs for faster training.
2.  **Balance Fairness**: Apply "Weights" so the model doesn't ignore rare activities.
3.  **Monitor Quality**: Save the "Best" version of the model and stop training if the model stops improving.

---

## 💻 Code Walkthrough

### 1. Hardware Detection
```python
21:         gpus = tf.config.list_physical_devices('GPU')
22:         if gpus:
23:             print(f"✅ Found {len(gpus)} GPU(s). Acceleration is ACTIVE.")
29:             print("⚠️ No dedicated hardware acceleration (GPU/DirectML) found.")
```
-   **Lines 21-29**: Checks if TensorFlow can "see" an NVIDIA GPU (CUDA) or a Windows DirectML device. Training on a GPU is often 10x-50x faster than a CPU for this project.

### 2. Strategic Class Weighting
```python
65:         weights = class_weight.compute_class_weight('balanced', classes=classes, y=y_train)
73:                 weight_dict[fall_idx] *= 2.0
```
-   **Line 65**: Automatically calculates weights to balance the dataset. If you have 10 times more "Walk" than "Fall", the "Fall" samples will be weighted 10 times more heavily.
-   **Line 73**: **Fall Priority**. We manually multiply the "Fall" weight by an extra `2.0`. This tells the model: "Missing a Fall is twice as bad as missing any other movement." This is a critical safety feature of the HAR system.

### 3. Model Callbacks (Automation)
```python
37:             tf.keras.callbacks.EarlyStopping(
38:                 monitor='val_loss',
39:                 patience=10,
40:                 restore_best_weights=True
43:             tf.keras.callbacks.ReduceLROnPlateau(
45:                 factor=0.5,
50:             tf.keras.callbacks.ModelCheckpoint(
51:                 f'best_model_fold_{fold}.keras',
```
-   **Line 37-40**: **EarlyStopping**. If the model's accuracy on the validation set hasn't improved in 10 rounds (Epochs), the "Coach" stops the training to prevent **Overfitting**.
-   **Line 43-45**: **Learning Rate Decay**. If the model is struggling to learn more, we cut the learning rate in half (factor 0.5). This allows the model to "fine-tune" its weights.
-   **Line 50-51**: **ModelCheckpoint**. Saves the model file *only* if it achieved a new highest score. This ensures you always have the "Peak Performance" model at the end.

---

---

## 🎓 Concept Deep-Dives

### 1. What is GPU Acceleration?
A **CPU** (Central Processing Unit) is like a genius professor—it can solve any complex problem one at a time. A **GPU** (Graphics Processing Unit) is like 1,000 elementary students—each can only do simple math, but they do it all at the same time.
- **In our project**: Neural networks require millions of simple multiplications (Matrix Math).
- **The Benefit (Line 21)**: By using the GPU, the model can look at 64 samples at once, finishing training in minutes instead of hours.

### 2. What are Training Callbacks?
Training a model is like baking a cake. If you leave it in too long, it burns (**Overfitting**). If you take it out too soon, it's raw.
- **EarlyStopping (Line 37)**: This is like an oven with a sensor that stops the heat the moment the cake is perfectly brown.
- **ModelCheckpoint (Line 50)**: This is like a robotic arm that saves a copy of the cake every minute, but only throws away the old ones if the new one looks better.

---

## 🔗 Related Notes & Dependencies
- **Data Source**: The trainer receives data batches from the [loader.md](file:///d:/Projects/major/notes/fall_detector_logic/src/data/loader.md).
- **Model Architecture**: It trains the hybrid network defined in [cnn_gru.md](file:///d:/Projects/major/notes/fall_detector_logic/src/models/cnn_gru.md).
- **Configuration**: Patience levels and epochs are controlled via [settings.md](file:///d:/Projects/major/notes/fall_detector_logic/config/settings.md).

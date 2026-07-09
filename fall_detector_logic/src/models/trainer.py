import os
import numpy as np
import tensorflow as tf
from sklearn.utils import class_weight
from config import settings

class ModelTrainer:
    """
    Handles the training loop, callbacks, and class balancing for the CNN-GRU model.
    """
    def __init__(self, model):
        self.model = model
        
        # === GPU MEMORY FIXES (critical for 4GB RTX 3050) ===
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            try:
                # Grow only as needed to avoid OOM
                tf.config.experimental.set_memory_growth(gpus[0], True)
                print(f"✅ Using RTX 3050 GPU with dynamic memory growth")
            except RuntimeError as e:
                print(e)

        # === MIXED PRECISION (saves ~50% VRAM + huge speed boost) ===
        try:
            tf.keras.mixed_precision.set_global_policy('mixed_float16')
            print("✅ Mixed FP16 enabled → training on 4GB GPU now possible")
        except Exception as e:
            print(f"Mixed precision not supported or already set: {e}")
        self._check_gpu_status()

    def _check_gpu_status(self):
        """
        Detects available GPUs or DirectML devices. 
        TensorFlow handles the fallback to CPU automatically, but this provides 
        explicit feedback to the user.
        """
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"✅ Found {len(gpus)} GPU(s). Acceleration is ACTIVE.")
            for gpu in gpus:
                print(f"  - Device: {gpu.name}")
        else:
            # Check for DirectML specifically if standard GPU list is empty
            # (Sometimes DirectML devices show up under a different check or the same one)
            print("⚠️ No dedicated hardware acceleration (GPU/DirectML) found.")
            print("ℹ️ Falling back to CPU training mode.")

    def get_callbacks(self, fold=0):
        """
        Setup early stopping, learning rate reduction, and model checkpointing.
        """
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=settings.EARLY_STOPPING_PATIENCE,
                restore_best_weights=True,
                verbose=1
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=min(5, settings.EARLY_STOPPING_PATIENCE // 2),
                min_lr=1e-6,
                verbose=1
            ),
            tf.keras.callbacks.ModelCheckpoint(
                os.path.join(settings.MODEL_DIR, f'best_model_fold_{fold}.keras'),
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
        return callbacks

    def compute_class_weights(self, y_train):
        """
        Compute class weights to penalize the model heavily for missing fall events.
        """
        classes = np.unique(y_train)
        weights = class_weight.compute_class_weight('balanced', classes=classes, y=y_train)
        weight_dict = dict(zip(classes, weights))
        
        # Priority: Fall detection is the primary goal
        if 'fall' in settings.CLASSES:
            fall_idx = settings.CLASSES.index('fall')
            if fall_idx in weight_dict:
                # Multiply fall weight by 2x (combined with focal alpha 0.40 for strong recall)
                weight_dict[fall_idx] *= 2.0
                print(f"  - Prioritizing 'fall' class (Index {fall_idx}) with 2x weight multiplier")
                
        return weight_dict

    def train(self, X_train, y_train, X_val, y_val, fold=0):
        """
        Execute the training loop.
        """
        class_weights = self.compute_class_weights(y_train)
        
        print("\n--- Training Model ---")
        print(f"Class Weights applied: {class_weights}")
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=settings.EPOCHS,
            batch_size=settings.BATCH_SIZE,
            class_weight=class_weights,
            callbacks=self.get_callbacks(fold),
            verbose=1
        )
        return history


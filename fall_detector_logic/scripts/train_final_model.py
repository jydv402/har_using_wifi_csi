import os
import sys
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split

# Ensure project root is in PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from src.data.loader import UniversalDataLoader
from src.models.cnn_gru import build_cnn_gru_model
from src.models.trainer import ModelTrainer

def run_final_training():
    # 1. Identify all files and split by SESSION (not by window)
    loader = UniversalDataLoader()
    all_files = []
    
    # Collect all files from original data folders
    data_folders = getattr(settings, 'DATA_FOLDERS', settings.CLASSES)
    for folder in data_folders:
        cls_dir = settings.RAW_DATA_DIR / folder
        if cls_dir.exists():
            all_files.extend(list(cls_dir.glob("*.csv")))
            
    if not all_files:
        print("Error: No training data found.")
        return

    # Split files into Train and Val (80/20)
    # This prevents the 75% overlap 'leakage' between adjacent windows
    from sklearn.model_selection import train_test_split
    train_files, val_files = train_test_split(all_files, test_size=0.2, random_state=42)
    
    print(f"Split {len(all_files)} files into {len(train_files)} train and {len(val_files)} val sessions.")

    # 2. Load windows from the distinct sessions
    X_train, y_train = loader.load_dataset(file_list=train_files, normalize=settings.NORMALIZE)
    X_val, y_val = loader.load_dataset(file_list=val_files, normalize=settings.NORMALIZE, augment=False)
    
    if X_train is None or len(X_train) == 0:
        print("Error: Failed to load training data.")
        return
    
    print(f"\n--- Dataset Summary ---")
    print(f"X_train shape: {X_train.shape}")
    print(f"X_val shape: {X_val.shape}")
    
    # 3. Build Model
    input_shape = (settings.WINDOW_SIZE, settings.FEATURES)
    num_classes = len(settings.CLASSES)
    model = build_cnn_gru_model(input_shape, num_classes)
    model.summary()

    # 4. Train
    trainer = ModelTrainer(model)
    history = trainer.train(X_train, y_train, X_val, y_val)

    # 5. Export
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    
    # Save Full Model in LEGACY H5 format for best compatibility (v7.0)
    final_model_path = settings.MODEL_DIR / "final_har_model.h5"
    model.save(final_model_path)
    
    # Also save weights specifically
    weights_path = settings.MODEL_DIR / "final_har_weights.h5"
    model.save_weights(weights_path)
    
    print(f"✅ Saved Legacy H5 model to {final_model_path}")
    print(f"✅ Saved weights-only to {weights_path}")
    
    print("\n--- Training Complete ---")
    print("NOTE: TFLite Export has been completely decoupled for efficiency.")
    print("Please run `python scripts/export_tflite.py` to compile the quantized TFLite edge model.")

if __name__ == "__main__":
    run_final_training()

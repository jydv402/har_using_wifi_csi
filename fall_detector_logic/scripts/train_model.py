import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data.preprocessor import CSIPreprocessor
from src.models.cnn_gru import build_cnn_gru_model
from src.models.trainer import ModelTrainer
from config import settings

def load_data_by_session():
    """
    Load raw CSV data with SESSION-LEVEL split to prevent window overlap leakage.
    Returns (X_train, y_train, X_val, y_val) with no shared windows between splits.
    """
    preprocessor = CSIPreprocessor()
    
    print("\n--- Collecting Files ---")
    
    # 1. Collect all files grouped by data folder, mapped to new class indices
    all_files = []
    all_labels = []
    
    class_to_idx = {cls: i for i, cls in enumerate(settings.CLASSES)}
    data_folders = getattr(settings, 'DATA_FOLDERS', settings.CLASSES)
    class_map = getattr(settings, 'CLASS_MAP', {c: c for c in settings.CLASSES})
    
    for folder in data_folders:
        dir_path = Path(settings.RAW_DATA_DIR) / folder
        if not dir_path.exists():
            print(f"Warning: Directory {dir_path} not found. Skipping {folder}.")
            continue
        
        mapped_class = class_map.get(folder, folder)
        if mapped_class not in class_to_idx:
            continue
        label_idx = class_to_idx[mapped_class]
            
        files = sorted(dir_path.glob("*.csv"))
        print(f"Found {len(files)} files for {folder} → {mapped_class}")
        
        all_files.extend(files)
        all_labels.extend([label_idx] * len(files))
    
    if not all_files:
        raise ValueError("No data found! Please run collect_data.py first.")
    
    # 2. Session-level split: split FILES, not windows
    train_files, val_files, train_file_labels, val_file_labels = train_test_split(
        all_files, all_labels, test_size=0.2, random_state=42, stratify=all_labels
    )
    
    print(f"\nSession split: {len(train_files)} train files, {len(val_files)} val files")
    
    # 3. Load windows from each split independently
    def load_windows(file_list, file_labels):
        X_list = []
        y_list = []
        for file_path, label_idx in zip(file_list, file_labels):
            csi_matrix = _load_csv_features(file_path)
            if csi_matrix is None:
                continue
                
            windows = preprocessor.create_overlapping_windows(
                csi_matrix, 
                window_size=settings.WINDOW_SIZE, 
                hop_size=settings.HOP_SIZE
            )
            
            if len(windows) > 0:
                X_list.append(windows)
                y_list.append(np.full(len(windows), label_idx))
        
        if not X_list:
            return np.array([]), np.array([])
        return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0)
    
    X_train, y_train = load_windows(train_files, train_file_labels)
    X_val, y_val = load_windows(val_files, val_file_labels)
    
    print(f"Train windows: {len(X_train)}, Val windows: {len(X_val)}")
    print(f"Window shape: {X_train.shape[1:]}")
    
    return X_train, y_train, X_val, y_val


def _load_csv_features(file_path):
    """Load a single CSV and return only the 52 amplitude columns."""
    try:
        with open(file_path, 'r') as f:
            first_line = f.readline()
        
        has_header = any(c.isalpha() for c in first_line)
        header_val = 0 if has_header else None
        df = pd.read_csv(file_path, header=header_val)
        
        csv_cols = len(df.columns)
        if csv_cols >= 57:
            if settings.INCLUDE_METADATA:
                csi_matrix = df.iloc[:, 1:57].values.astype(np.float32)
            else:
                csi_matrix = df.iloc[:, 5:57].values.astype(np.float32)
        else:
            csi_matrix = df.values.astype(np.float32)
        return csi_matrix
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def main(export_only=False):
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    
    X_train_raw, y_train, X_val_raw, y_val = load_data_by_session()
    
    if len(X_train_raw) == 0:
        print("Error: No training data loaded.")
        return
    
    # Preprocess (Fit Scaler on TRAINING data only, then transform both)
    preproc = CSIPreprocessor()
    preproc.fit_scaler(X_train_raw)
    preproc.save(os.path.join(settings.MODEL_DIR, "scaler.pkl"))
    
    print("\nApplying Preprocessing Filter and Normalization...")
    
    def preprocess_split(X_raw):
        X_clean = np.zeros_like(X_raw)
        for i in range(len(X_raw)):
            filtered = preproc.remove_outliers(X_raw[i])
            X_clean[i] = preproc.transform(np.expand_dims(filtered, axis=0))[0]
        return X_clean
    
    X_train = preprocess_split(X_train_raw)
    X_val = preprocess_split(X_val_raw)
    
    # Data augmentation — only on training data
    print("Applying Data Augmentation...")
    X_aug_list = [X_train]
    y_aug_list = [y_train]
    for i in range(len(X_train)):
        augmented = preproc.augment_window(X_train[i])
        X_aug_list.append(np.expand_dims(augmented, axis=0))
        y_aug_list.append(np.array([y_train[i]]))
    X_train = np.concatenate(X_aug_list, axis=0)
    y_train = np.concatenate(y_aug_list, axis=0)
    print(f"After augmentation: {len(X_train)} train windows, {len(X_val)} val windows")
        
    num_classes = len(settings.CLASSES)
    input_shape = (settings.WINDOW_SIZE, settings.FEATURES)
    
    # Build and train a single model (no misleading KFold wrapper)
    print("\nTraining Model...")
    model = build_cnn_gru_model(input_shape, num_classes)
    trainer = ModelTrainer(model)
    
    if not export_only:
        trainer.train(X_train, y_train, X_val, y_val, fold=0)
    
    # Save the final model
    best_weights_path = os.path.join(settings.MODEL_DIR, f'best_model_fold_0.keras')
    if os.path.exists(best_weights_path):
        model.load_weights(best_weights_path)
    
    final_model_path = os.path.join(settings.MODEL_DIR, 'final_har_model.keras')
    model.save(final_model_path)
    print(f"\nSaved Keras model to {final_model_path}")
    print("Run `python scripts/export_tflite.py` separately for TFLite export.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-only", action="store_true", help="Skip training and just export the existing h5 model to tflite.")
    args = parser.parse_args()
    main(export_only=args.export_only)

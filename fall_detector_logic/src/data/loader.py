import os
import numpy as np
import pandas as pd
from pathlib import Path
from config import settings
from src.data.preprocessor import CSIPreprocessor

class UniversalDataLoader:
    """
    A unified data loader that reads processed CSVs from data/raw/
    and returns X, y as NumPy arrays.
    """
    def __init__(self, window_size=settings.WINDOW_SIZE, hop_size=settings.HOP_SIZE):
        self.window_size = window_size
        self.hop_size = hop_size
        self.preprocessor = CSIPreprocessor()
        
        self.data_dir = settings.RAW_DATA_DIR
        self.classes = settings.CLASSES
        self.class_to_idx = {cls: i for i, cls in enumerate(self.classes)}
        # Folder-to-class mapping for merged class structure
        self.data_folders = getattr(settings, 'DATA_FOLDERS', settings.CLASSES)
        self.class_map = getattr(settings, 'CLASS_MAP', {c: c for c in self.classes})

    def augment_data(self, windows, labels):
        """
        Synthetically increases dataset size for minority classes (Upsampling)
        and prunes majority classes (Downsampling) to achieve strict balance.
        """
        unique_classes, counts = np.unique(labels, return_counts=True)
        # Use a fixed target per class for absolute balance
        target_per_class = getattr(settings, 'AUG_MAX_SAMPLES_PER_CLASS', 12000)
        
        balanced_X = []
        balanced_y = []
        
        print(f"\n--- Balancing Dataset (Target: {target_per_class} samples/class) ---")
        for cls_idx, count in zip(unique_classes, counts):
            cls_name = self.classes[cls_idx]
            cls_indices = np.where(labels == cls_idx)[0]
            
            if count > target_per_class:
                # DOWNSAMPLE
                print(f"  - Pruning {cls_name}: {count} -> {target_per_class}")
                keep_indices = np.random.choice(cls_indices, size=target_per_class, replace=False)
                balanced_X.append(windows[keep_indices])
                balanced_y.append(labels[keep_indices])
            elif count < target_per_class:
                # UPSAMPLE (Augment)
                print(f"  - Augmenting {cls_name}: {count} -> {target_per_class}")
                # Keep original data
                balanced_X.append(windows[cls_indices])
                balanced_y.append(labels[cls_indices])
                
                # Create augmented samples
                needed = target_per_class - count
                aug_indices = np.random.choice(cls_indices, size=needed, replace=True)
                
                cls_augmented = []
                for idx in aug_indices:
                    window = windows[idx].copy()
                    
                    # Apply random transformation (v6.0 Masking)
                    rand = np.random.random()
                    if rand < 0.4:
                        # Time Mask: Zero out a random 10% block of time
                        size = int(window.shape[0] * 0.1)
                        start = np.random.randint(0, window.shape[0] - size)
                        window[start:start+size, :] = 0
                    elif rand < 0.8:
                        # Frequency (Subcarrier) Mask: Zero out 4 random subcarriers
                        sc_indices = np.random.choice(window.shape[1], 4, replace=False)
                        window[:, sc_indices] = 0
                    else:
                        # Amplitude variation
                        scale = np.random.uniform(0.8, 1.2)
                        window = window * scale
                    
                    cls_augmented.append(window)
                
                balanced_X.append(np.array(cls_augmented))
                balanced_y.append(np.full(needed, cls_idx))
            else:
                # Already balanced
                balanced_X.append(windows[cls_indices])
                balanced_y.append(labels[cls_indices])
        
        final_X = np.concatenate(balanced_X)
        final_y = np.concatenate(balanced_y)
            
        return final_X, final_y

    def load_dataset(self, file_list=None, normalize=settings.NORMALIZE, augment=True):
        """
        Loads and processes data. 
        If file_list is provided, only loads those specific files (prevents leakage).
        """
        print(f"Loading {'partial' if file_list else 'full'} dataset from raw CSV files...")
        all_windows = []
        all_labels = []
        
        # If no file list, find all files
        if file_list is None:
            file_list = []
            for folder in self.data_folders:
                cls_dir = self.data_dir / folder
                if cls_dir.exists():
                    file_list.extend(list(cls_dir.glob("*.csv")))
        
        # Group files by class for logging
        from collections import defaultdict
        files_by_class = defaultdict(list)
        for f in file_list:
            cls_name = f.parent.name
            if cls_name in self.data_folders:
                files_by_class[cls_name].append(f)

        for folder in self.data_folders:
            csv_files = files_by_class.get(folder, [])
            if not csv_files: continue
            
            mapped_class = self.class_map.get(folder, folder)
            if mapped_class not in self.class_to_idx: continue
            label_idx = self.class_to_idx[mapped_class]
            
            print(f"  - Loading {folder} → {mapped_class} ({len(csv_files)} files)")
            
            for i, file_path in enumerate(csv_files):
                try:
                    with open(file_path, 'r') as f:
                        first_line = f.readline()
                    
                    has_header = any(c.isalpha() for c in first_line)
                    header_val = 0 if has_header else None
                    df = pd.read_csv(file_path, header=header_val)

                    # Fix (v6.0): Explicitly skip timestamp (0) and metadata (1-4)
                    # Amplitudes are in columns 5-56 (52 total)
                    csv_cols = len(df.columns)
                    if csv_cols >= 57:
                        if settings.INCLUDE_METADATA:
                            # 1:rssi, 2:nf, 3:agc, 4:fft, 5-56:amps (56 total)
                            feature_data = df.iloc[:, 1:57].values.astype(np.float32)
                        else:
                            # Purely 52 Amplitudes
                            feature_data = df.iloc[:, 5:57].values.astype(np.float32)
                    else:
                        feature_data = df.values.astype(np.float32)

                    if len(feature_data) < self.window_size: continue
                        
                    # Preprocess
                    filtered_csi = self.preprocessor.remove_outliers(feature_data)
                    file_windows = self.preprocessor.create_overlapping_windows(
                        filtered_csi, self.window_size, self.hop_size
                    )
                    
                    if len(file_windows) > 0:
                        all_windows.append(file_windows)
                        all_labels.extend([label_idx] * len(file_windows))
                    
                    # Progress update for large sets
                    if (i + 1) % 100 == 0:
                        print(f"    ... processed {i + 1}/{len(csv_files)} files")
                        
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        
        if not all_windows:
            print("No data found!")
            return None, None
            
        X = np.vstack(all_windows)
        y = np.array(all_labels)
        
        
        # Balance dataset via strict balancing/augmentation
        if augment and getattr(settings, 'AUG_MAX_SAMPLES_PER_CLASS', 0) > 0:
            X, y = self.augment_data(X, y)
        else:
            print("Augmentation bypassed (AUG_MAX_SAMPLES_PER_CLASS == 0 or False).")
        
        if normalize:
            print("Normalizing dataset using Global Statistics (StandardScaler)...")
            orig_shape = X.shape
            X_flat = X.reshape(-1, orig_shape[-1]).astype(np.float32)
            
            # Use preprocessor instance (Unified Pipeline)
            self.preprocessor.fit_scaler(X_flat)
            X_normalized = self.preprocessor.transform(X_flat)
            
            # Reshape back to (Samples, Time, Subcarriers)
            X = X_normalized.reshape(orig_shape)
            
            # Save the scaler for inference alignment
            scaler_path = settings.MODEL_DIR / "scaler.pkl"
            self.preprocessor.save(scaler_path)
            print(f"Global scaler saved to {scaler_path}")

        print(f"Total samples after augmentation: {len(X)} across {len(np.unique(y))} classes.")
        return X, y

if __name__ == "__main__":
    # Test loading
    loader = UniversalDataLoader()
    X, y = loader.load_dataset()
    if X is not None:
        print(f"Final X shape: {X.shape}, y shape: {y.shape}")

import numpy as np
from scipy.signal import medfilt
from sklearn.preprocessing import StandardScaler
import joblib
import os

from config import settings

class CSIPreprocessor:
    """
    Robust preprocessing pipeline for CSI data.
    Implements Median filtering for outlier removal and Z-score normalization.
    """
    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False

    def remove_outliers(self, csi_matrix):
        """
        Applies a median filter frame-by-frame or across time to remove impulse noise.
        If APPLY_CLEANING is False, returns pure data.
        """
        if not getattr(settings, 'APPLY_CLEANING', True):
            return csi_matrix
        
        # DC removal: subtract per-subcarrier mean to remove environment-dependent offset
        csi_matrix = csi_matrix - np.mean(csi_matrix, axis=0, keepdims=True)
            
        filtered = np.zeros_like(csi_matrix)
        # Apply median filter along the time axis for each subcarrier
        for i in range(csi_matrix.shape[1]):
            filtered[:, i] = medfilt(csi_matrix[:, i], kernel_size=settings.DENOISE_KERNEL)
        return filtered

    def fit_scaler(self, csi_matrix):
        """Fit the standard scaler on a training dataset."""
        # Flatten the time dimension to fit properly across subcarriers
        flat_data = csi_matrix.reshape(-1, csi_matrix.shape[-1])
        self.scaler.fit(flat_data)
        self.is_fitted = True

    def transform(self, csi_matrix):
        """Apply Z-score normalization."""
        if not self.is_fitted and settings.NORMALIZE:
            raise ValueError("Scaler has not been fitted yet!")

        if settings.NORMALIZE:
            original_shape = csi_matrix.shape
            flat_data = csi_matrix.reshape(-1, original_shape[-1])
            normalized = self.scaler.transform(flat_data)
            return normalized.reshape(original_shape)
        
        return csi_matrix

    def create_overlapping_windows(self, csi_matrix, window_size, hop_size):
        """
        Transform continuous CSI data into overlapping windows for CNN/GRU input.
        Returns: numpy array of shape (Samples, WindowSize, Subcarriers)
        """
        num_windows = (len(csi_matrix) - window_size) // hop_size + 1
        if num_windows <= 0:
            return np.array([])

        windows = np.array([
            csi_matrix[i * hop_size : i * hop_size + window_size]
            for i in range(num_windows)
        ])
        return windows

    def process_live_window(self, csi_window):
        """
        Fast-path processing for real-time inference window.
        Input shape: (WindowSize, Subcarriers)
        """
        filtered = self.remove_outliers(csi_window)
        # Expanding dims to simulate a batch of 1
        normalized = self.transform(np.expand_dims(filtered, axis=0))
        return normalized

    # ── Data Augmentation Methods ─────────────────────────────────────────────

    def augment_time_shift(self, csi_window, max_shift=5):
        """Circular time-shift augmentation. Shifts CSI packets along time axis."""
        shift = np.random.randint(-max_shift, max_shift + 1)
        return np.roll(csi_window, shift, axis=0)

    def augment_noise(self, csi_window, noise_std=0.05):
        """Additive Gaussian noise to simulate environmental variance."""
        noise = np.random.normal(0, noise_std, csi_window.shape).astype(np.float32)
        return csi_window + noise

    def augment_amplitude_scale(self, csi_window, scale_range=(0.8, 1.2)):
        """Random per-subcarrier amplitude scaling to simulate RSSI variations."""
        scales = np.random.uniform(scale_range[0], scale_range[1], 
                                   size=(1, csi_window.shape[1])).astype(np.float32)
        return csi_window * scales

    def augment_window(self, csi_window):
        """Apply all augmentations randomly to a single window."""
        augmented = csi_window.copy()
        if np.random.random() > 0.5:
            augmented = self.augment_time_shift(augmented)
        if np.random.random() > 0.5:
            augmented = self.augment_noise(augmented)
        if np.random.random() > 0.5:
            augmented = self.augment_amplitude_scale(augmented)
        return augmented

    def save(self, filepath):
        """Save the fitted scaler to disk."""
        if self.is_fitted:
            joblib.dump(self.scaler, filepath)
            print(f"Scaler saved to {filepath}")

    def load(self, filepath):
        """Load a fitted scaler from disk."""
        if os.path.exists(filepath):
            self.scaler = joblib.load(filepath)
            self.is_fitted = True
            print(f"Scaler loaded from {filepath}")
        else:
            print(f"Scaler file not found: {filepath}")

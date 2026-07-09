import os
import sys
import numpy as np
import tensorflow as tf
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import pandas as pd

# Ensure project root is in PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from src.data.loader import UniversalDataLoader

def analyze_model_performance():
    # 1. Load Data
    loader = UniversalDataLoader()
    X, y = loader.load_dataset(normalize=settings.NORMALIZE)
    
    if X is None:
        print("No data found.")
        return

    # 2. Check Distribution
    print("\n--- Class Distribution ---")
    class_counts = {}
    for i, cls in enumerate(settings.CLASSES):
        count = np.sum(y == i)
        class_counts[cls] = count
        print(f"{cls:<10}: {count} samples ({count/len(y):.1%})")

    # 3. Model & Prediction
    model_path = settings.MODEL_DIR / "best_model_fold_0.keras"
    if not model_path.exists():
        # Fallback to final model
        model_path = settings.MODEL_DIR / "final_har_model.keras"
        
    if not model_path.exists():
        print(f"Model not found at {model_path}")
        return
        
    print(f"\nLoading model: {model_path}")
    model = tf.keras.models.load_model(model_path, compile=False)
    
    # Stratified Split (same as training)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("\nRunning validation predictions...")
    y_pred_probs = model.predict(X_val, verbose=1)
    y_pred = np.argmax(y_pred_probs, axis=1)

    # 4. Metrics
    print("\n--- Classification Report ---")
    present_classes = [settings.CLASSES[i] for i in np.unique(y_val)]
    print(classification_report(y_val, y_pred, target_names=present_classes))

    print("\n--- Confusion Matrix ---")
    cm = confusion_matrix(y_val, y_pred)
    cm_df = pd.DataFrame(cm, index=present_classes, columns=present_classes)
    print(cm_df)

if __name__ == "__main__":
    analyze_model_performance()

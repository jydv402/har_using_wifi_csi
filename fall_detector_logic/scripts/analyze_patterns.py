import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from src.data.loader import UniversalDataLoader

def analyze_patterns():
    print("--- CSI Pattern Analysis ---")
    loader = UniversalDataLoader()
    # Load without normalization to see raw stats
    X, y = loader.load_dataset(normalize=False, augment=False)
    
    if X is None:
        print("No data found.")
        return

    classes = settings.CLASSES
    
    stats = []
    
    for i, cls_name in enumerate(classes):
        indices = np.where(y == i)[0]
        if len(indices) == 0:
            continue
            
        cls_data = X[indices] # (Samples, Time, Subcarriers)
        
        # Calculate temporal variance (indicator of motion)
        # Take variance across the time axis for each sample/subcarrier
        # then mean across subcarriers and samples.
        sample_var = np.var(cls_data, axis=1) # (Samples, Subcarriers)
        mean_var = np.mean(sample_var)
        
        # Calculate absolute mean amplitude
        mean_amp = np.mean(cls_data)
        
        # Calculate "Activity Index" (Variance / Mean)
        # Higher index = more relative disturbance
        activity_index = mean_var / (mean_amp + 1e-6)
        
        print(f"\n[{cls_name.upper()}]")
        print(f"  Samples: {len(cls_data)}")
        print(f"  Mean Amplitude: {mean_amp:.2f}")
        print(f"  Temporal Variance: {mean_var:.2f}")
        print(f"  Activity Index: {activity_index:.4f}")
        
        stats.append({
            "class": cls_name,
            "mean_amp": mean_amp,
            "variance": mean_var,
            "activity": activity_index
        })

    # Compare classes
    df = pd.DataFrame(stats)
    print("\n--- Comparative Analysis ---")
    print(df.sort_values("activity", ascending=False))
    
    # Save a visualization of the mean variance
    plt.figure(figsize=(10, 6))
    plt.bar(df["class"], df["variance"], color='skyblue')
    plt.title("Mean Temporal Variance per Class (Motion Intensity)")
    plt.ylabel("Variance")
    plt.savefig("evaluation/class_variance_patterns.png")
    print("\nPattern visualization saved to evaluation/class_variance_patterns.png")

if __name__ == "__main__":
    os.makedirs("evaluation", exist_ok=True)
    analyze_patterns()

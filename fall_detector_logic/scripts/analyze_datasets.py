import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure project root is in PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from config import settings

def analyze_class_stats():
    raw_dir = Path(settings.RAW_DATA_DIR)
    classes = settings.CLASSES
    
    print("\n" + "="*60)
    print(f"{'Class':<12} | {'Samples':<8} | {'Mean Amp':<10} | {'Std Dev':<8}")
    print("-" * 60)
    
    summary = []
    
    for cls in classes:
        cls_path = raw_dir / cls
        if not cls_path.exists():
            continue
            
        files = list(cls_path.glob("*.csv"))
        if not files:
            continue
            
        # Analyze first 10 files to get a profile
        all_means = []
        all_stds = []
        total_rows = 0
        
        for f in files[:15]: # Take a good sample size
            try:
                # Detect header
                with open(f, 'r') as file:
                    first_line = file.readline()
                has_header = any(c.isalpha() for c in first_line)
                h = 0 if has_header else None
                
                df = pd.read_csv(f, header=h)
                
                # Extract CSI subcarriers (skip timestamp/rssi)
                if df.shape[1] >= settings.SUBCARRIERS + 2:
                    data = df.iloc[:, 2:settings.SUBCARRIERS+2].values.astype(np.float32)
                else:
                    data = df.values.astype(np.float32)
                    
                all_means.append(np.mean(data))
                all_stds.append(np.std(data))
                total_rows += len(data)
            except Exception as e:
                # print(f"Error: {e}")
                continue
        
        if all_means:
            avg_mean = np.mean(all_means)
            avg_std = np.mean(all_stds)
            print(f"{cls:<12} | {len(files):<8} | {avg_mean:10.2f} | {avg_std:8.2f}")
            summary.append({
                "class": cls,
                "mean": avg_mean,
                "std": avg_std,
                "files": len(files)
            })

    print("=" * 60)
    print("\n🔍 DIAGNOSTIC INSIGHTS:")
    
    if not summary:
        print("❌ No data found to analyze.")
        return

    # Check for anomalies
    empty_profile = next((s for s in summary if s['class'] == 'empty'), None)
    if empty_profile and empty_profile['mean'] < 0.1:
        print("⚠️  WARNING: Your 'empty' dataset has near-zero amplitude!")
    
    fall_profile = next((s for s in summary if s['class'] == 'fall'), None)
    if empty_profile and fall_profile:
        ratio = fall_profile['std'] / (empty_profile['std'] + 1e-6)
        print(f"✅ Class Contrast (Fall vs Empty Variance): {ratio:.2f}x")
        if ratio < 1.5:
             print("⚠️  WARNING: Fall variance is very similar to Empty. Detection will be difficult.")

if __name__ == "__main__":
    analyze_class_stats()

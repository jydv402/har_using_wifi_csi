import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import tensorflow as tf

sys.path.append(str(Path(__file__).parent.parent))
from config import settings
from src.data.preprocessor import CSIPreprocessor

def get_calibration_data(num_samples=200):
    """
    Ultra-fast dataloader specifically designed for pulling a tiny subset 
    of un-augmented raw CSV windows strictly for INT8 TFLite calibration.
    """
    print("Extracting rapid calibration dataset...")
    preprocessor = CSIPreprocessor()
    
    # Needs the exact scaler the model was trained on
    scaler_path = settings.MODEL_DIR / "scaler.pkl"
    if scaler_path.exists():
        preprocessor.load(scaler_path)
    else:
        print("Warning: scaler.pkl not found! TFLite accuracy may be impacted.")

    X_list = []
    count = 0
    
    data_folders = getattr(settings, 'DATA_FOLDERS', settings.CLASSES)
    for activity in data_folders:
        dir_path = settings.RAW_DATA_DIR / activity
        if not dir_path.exists():
            continue
            
        # Target only the first two CSVs of an activity. Extremely low cost!
        csv_files = list(dir_path.glob("*.csv"))[:2]
        
        for file in csv_files:
            try:
                with open(file, 'r') as f:
                    first_line = f.readline()
                has_header = any(c.isalpha() for c in first_line)
                header_val = 0 if has_header else None
                
                df = pd.read_csv(file, header=header_val)

                if settings.INCLUDE_METADATA:
                    feature_data = df.iloc[:, 1:57].values.astype(np.float32)
                else:
                    feature_data = df.iloc[:, 5:57].values.astype(np.float32)

                if len(feature_data) < settings.WINDOW_SIZE: 
                    continue

                filtered_csi = preprocessor.remove_outliers(feature_data)
                windows = preprocessor.create_overlapping_windows(filtered_csi, settings.WINDOW_SIZE, settings.HOP_SIZE)
                
                if len(windows) > 0:
                    X_list.append(windows)
                    count += len(windows)
                    
                if count >= num_samples:
                    break
            except Exception as e:
                print(f"Skipping {file.name}: {e}")
                
        if count >= num_samples:
            break
            
    if not X_list:
        return None

    X_raw = np.vstack(X_list)[:num_samples]
    
    # TFLite Quantization requires the inputs to be IDENTICAL scale to normal model inputs
    orig_shape = X_raw.shape
    X_flat = X_raw.reshape(-1, orig_shape[-1])
    X_norm = preprocessor.transform(X_flat).reshape(orig_shape)
    
    return X_norm

def export_tflite_only():
    print("Loading Existing Dynamic Keras Model...")
    keras_path = settings.MODEL_DIR / "final_har_model.keras"
    if not keras_path.exists():
        print("Error: Train the Keras model first using train_final_model.py!")
        return
        
    # compile=False allows weights to be parsed without instantiating custom losses.
    dynamic_model = tf.keras.models.load_model(str(keras_path), compile=False)

    print("Rebuilding Model as STATIC (batch_size=1) to eliminate GRU TensorLists...")
    from src.models.cnn_gru import build_cnn_gru_model
    
    input_shape = (settings.WINDOW_SIZE, settings.FEATURES)
    num_classes = len(settings.CLASSES)
    
    # Passing batch_size=1 forces the TF compiler to unroll the GRU loops permanently natively!
    static_model = build_cnn_gru_model(input_shape, num_classes, batch_size=1)
    
    # Transfer trained weights from dynamic graph to static graph
    static_model.set_weights(dynamic_model.get_weights())
    print("✅ Weights transferred successfully to Static Edge Model.")

    X_calib = get_calibration_data(num_samples=300)
    if X_calib is None or len(X_calib) == 0:
        print("Error: No data found for calibration. Cannot quantize.")
        return
        
    print(f"Successfully loaded {len(X_calib)} pure frames for converter profiling.")

    converter = tf.lite.TFLiteConverter.from_keras_model(static_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.int8]
    
    # Fully standard compilation. No hacky SELECT_TF_OPS needed since loops are statically unrolled!
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    def representative_data_gen():
        for i in range(len(X_calib)):
            sample = np.expand_dims(X_calib[i], axis=0).astype(np.float32)
            yield [sample]

    converter.representative_dataset = representative_data_gen
    
    print("Compiling Pure INT8 Edge Model natively... Please wait.")
    tflite_model = converter.convert()

    tflite_path = settings.MODEL_DIR / "har_model_quantized.tflite"
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)
        
    size_kb = len(tflite_model) / 1024
    print(f"✅ SUCCESS! INT8 TFLite exported: {tflite_path.name} ({size_kb:.1f} KB)")
    print("The model is perfectly structured to natively handle the Inference Dashboard!")

if __name__ == "__main__":
    export_tflite_only()

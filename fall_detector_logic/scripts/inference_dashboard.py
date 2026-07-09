import os
import sys
import time
import argparse
import threading
import csv
import numpy as np
import requests
from datetime import datetime
from pathlib import Path



# Provide cleaner TF logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf

# Ensure project root is in PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from src.utils.serial_utils import AsyncSerialReader
from src.data.parser import CSIParser, CSIRingBuffer
from src.data.preprocessor import CSIPreprocessor
from src.models.cnn_gru import build_cnn_gru_model
from config import settings

class InferenceDashboard:
    """
    Real-time Human Activity Recognition Dashboard.
    Supports dynamic fallback between Keras (.keras) and TFLite (.tflite) inference backends.
    Now uses v6.0 architecture reconstruction for loading robustness.
    """
    def __init__(self, port, model_path, backend="keras", backend_url="https://fall-alert-backend-mdys.onrender.com/predictions"):
        self.port = port
        self.backend = backend.lower()
        self.backend_url = backend_url
        self.reader = AsyncSerialReader(port, settings.BAUD_RATE)
        self.parser = CSIParser()
        self.preprocessor = CSIPreprocessor()
        self.lock = threading.Lock()
        
        # Buffer for inference (Matching training window size)
        self.inf_buffer = CSIRingBuffer(
            window_size=settings.WINDOW_SIZE, 
            features=settings.FEATURES
        )
        
        self.classes = settings.CLASSES
        print(f"\n--- Initializing HAR Dashboard ({self.backend.upper()} Backend) ---")
        print(f"Loading Model: {model_path}...")
        
        # Load Model based on specific Backend string
        if self.backend == "keras":
            try:
                # v7.0 Fix: Prioritize Weight Loading (.h5) over Full Model Loading (.keras)
                # Reconstruct architecture from code (guarantees matching layers)
                input_shape = (settings.WINDOW_SIZE, settings.FEATURES)
                num_classes = len(self.classes)
                self.model = build_cnn_gru_model(input_shape, num_classes)
                
                # Check for weights-only file first
                weights_path = settings.MODEL_DIR / "final_har_weights.h5"
                if weights_path.exists():
                    self.model.load_weights(str(weights_path))
                    print(f"✅ Loaded H5 weights from {weights_path}")
                else:
                    # Fallback to .keras full model loading (reconstruct + weight extraction)
                    self.model.load_weights(model_path)
                    print(f"✅ Loaded weights from {model_path}")
                
                print("✅ Keras model initialized and weights loaded!")
            except Exception as e:
                print(f"Error loading Keras model: {e}")
                print("\nCRITICAL: Model architecture or weights mismatch.")
                print("Action: Run `python scripts/train_final_model.py` to generate matching v7.0 weights.")
                sys.exit(1)
        elif self.backend == "tflite":
            try:
                self.interpreter = tf.lite.Interpreter(model_path=str(model_path))
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                print(f"✅ TFLite Interpreter Allocated! Input DType: {self.input_details[0]['dtype']}")
            except ValueError as e:
                print(f"Failed to load TFLite model: {e}")
                sys.exit(1)
        else:
            print(f"Unknown backend: {self.backend}")
            sys.exit(1)
            
        # Load Global Scaler
        scaler_path = settings.MODEL_DIR / "scaler.pkl"
        if scaler_path.exists():
            self.preprocessor.load(scaler_path)
            print(f"✅ Loaded global scaler from {scaler_path}")
        else:
            print(f"⚠️ WARNING: Global scaler NOT FOUND at {scaler_path}. Inference may fail mathematically.")
            
        self.is_running = False
        
        # Dashboard State
        self.latest_prediction = "Waiting..."
        self.latest_probs = np.zeros(len(self.classes))
        self.smoothed_probs = np.zeros(len(self.classes))
        self.label_history = []  
        self.packets_received = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0
        
        # Alert State (Keras specific functionality retained globally)
        self.consecutive_falls = 0
        self.last_alert_time = 0
        self.alert_message = ""
        self.alert_active_until = 0
        self.last_status_sent_time = 0

    def preprocess_window(self, window):
        """Applies global normalization using the fitted scaler."""
        filtered = self.preprocessor.remove_outliers(window)
        normalized = self.preprocessor.transform(filtered)
        return np.expand_dims(normalized, axis=0).astype(np.float32)

    def _log_fall(self, probability):
        """Logs fall event to logs/fall_history.csv."""
        log_dir = settings._ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "fall_history.csv"
        
        file_exists = log_file.exists()
        with open(log_file, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Date", "Probability"])
            
            now = datetime.now()
            writer.writerow([now.timestamp(), now.strftime("%Y-%m-%d %H:%M:%S"), f"{probability:.2f}"])

    def _handle_alerts(self, probs):
        """Standalone logic to handle fall alerts and journaling."""
        try:
            fall_idx = self.classes.index("fall")
        except ValueError:
            return
            
        fall_prob = probs[fall_idx]
        if fall_prob > settings.FALL_PROBABILITY_THRESHOLD:
            self.consecutive_falls += 1
            if self.consecutive_falls >= settings.CONSECUTIVE_DETECTIONS:
                now = time.time()
                if now - self.last_alert_time > settings.MIN_ALERT_INTERVAL:
                    self.alert_message = f"FALL DETECTED! Prob: {fall_prob:.1%}"
                    self.alert_active_until = now + 5.0
                    self.last_alert_time = now
                    self._log_fall(fall_prob)
                    self._send_backend_status("fall")
        else:
            self.consecutive_falls = 0
            now = time.time()
            # Send 'normal' status periodically (every 5 seconds) to heartbeat the backend
            if now - self.last_status_sent_time > 5.0:
                self._send_backend_status("normal")
                self.last_status_sent_time = now

    def _send_backend_status(self, status):
        """Sends the current status to the Render backend."""
        try:
            requests.post(self.backend_url, json={"status": status}, timeout=1.0)
        except requests.exceptions.RequestException:
            pass

    def inference_loop(self):
        """Background thread for performance-intensive model prediction."""
        alpha = 0.4 # EMA Smoothing factor (0=stiff, 1=instant)
        while self.is_running:
            try:
                if self.inf_buffer.has_window():
                    raw_window = self.inf_buffer.get_recent_window()
                    processed = self.preprocess_window(raw_window)
                    
                    if self.backend == "keras":
                        probs = self.model.predict(processed, verbose=0)[0]
                    else:
                        # TFLite Execution
                        input_dtype = self.input_details[0]['dtype']
                        if input_dtype == np.int8: 
                            scale, zero_point = self.input_details[0]['quantization']
                            processed = (processed / scale + zero_point).astype(np.int8)
                        else:
                            processed = processed.astype(input_dtype)

                        self.interpreter.set_tensor(self.input_details[0]['index'], processed)
                        self.interpreter.invoke()
                        probs = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                        
                        output_dtype = self.output_details[0]['dtype']
                        if output_dtype == np.int8: 
                            scale, zero_point = self.output_details[0]['quantization']
                            probs = (probs.astype(np.float32) - zero_point) * scale

                    pred_idx = np.argmax(probs)
                    max_prob = probs[pred_idx]
                    
                    with self.lock:
                        self.smoothed_probs = (alpha * probs) + ((1 - alpha) * self.smoothed_probs)
                        
                        # Apply Consensus & Confidence Threshold (v5.3)
                        consensus_size = getattr(settings, 'INFERENCE_CONSENSUS_SIZE', 3)
                        conf_threshold = getattr(settings, 'CONFIDENCE_THRESHOLD', 0.7)
                        
                        if max_prob >= conf_threshold:
                            self.label_history.append(self.classes[pred_idx])
                        else:
                            self.label_history.append("Uncertain")
                            
                        if len(self.label_history) > consensus_size:
                            self.label_history.pop(0)
                        
                        # Set prediction to the majority class in history
                        from collections import Counter
                        most_common = Counter(self.label_history).most_common(1)[0][0]
                        self.latest_prediction = most_common
                        
                        self._handle_alerts(probs)
                    
                    self.inf_buffer.advance_hop(settings.HOP_SIZE)
                else:
                    time.sleep(0.01)
            except Exception as e:
                # Catch inside the loop to prevent the thread from permanently dying
                with self.lock:
                    self.alert_message = f"Inference Error: {str(e)[:20]}"
                    self.alert_active_until = time.time() + 2.0
                time.sleep(0.05)
                # Force clear buffer to recover from corrupt frame
                self.inf_buffer.clear()

    def data_collection_loop(self):
        """High-priority thread for serial data intake."""
        while self.is_running:
            lines = self.reader.get_lines(max_lines=100)
            if lines:
                new_packets = 0
                for line in lines:
                    parsed = self.parser.parse_line(line)
                    if parsed:
                        amps = parsed["amplitudes"]
                        rssi = parsed["rssi"]
                        
                        if settings.INCLUDE_METADATA:
                            nf = parsed.get("noise_floor", -95)
                            agc = parsed.get("agc_gain", 0)
                            fft = parsed.get("fft_gain", 0)
                            feature_vector = np.concatenate(([rssi, nf, agc, fft], amps))
                        else:
                            feature_vector = amps
                        
                        self.inf_buffer.append(feature_vector)
                        new_packets += 1
                
                with self.lock:
                    self.packets_received += new_packets
                    self.frame_count += new_packets
            
            # FPS Calculation
            now = time.time()
            if now - self.last_fps_time >= 1.0:
                with self.lock:
                    self.fps = self.frame_count / (now - self.last_fps_time)
                    self.frame_count = 0
                    self.last_fps_time = now
                
            time.sleep(0.005)

    def render_dashboard(self):
        """Terminal UI rendering Loop with optimized ANSI updates."""
        # Use ANSI escape codes for colors
        CLR_RESET = "\033[0m"
        CLR_BOLD  = "\033[1m"
        CLR_FALL  = "\033[91m" 
        CLR_GOOD  = "\033[92m" 
        CLR_INFO  = "\033[94m" 
        CLR_GREY  = "\033[90m"
        ANSI_HOME = "\033[H"
        
        os.system('cls' if os.name == 'nt' else 'clear')
        
        while self.is_running:
            with self.lock:
                pred = self.latest_prediction
                probs = self.smoothed_probs.copy()
                fps = self.fps
                total = self.packets_received
                alert_msg = self.alert_message
                alert_active = time.time() < self.alert_active_until
                buffer_count = self.inf_buffer.count
                window_size = self.inf_buffer.window_size
                
            # Signal Diagnostics
            recent_avg = 0
            activity_index = 0
            if self.inf_buffer.has_window():
                window = self.inf_buffer.get_recent_window()
                recent_avg = np.mean(window)
                activity_index = np.var(window) / (recent_avg + 1e-6)

            out = []
            out.append(ANSI_HOME)
            out.append("="*80)
            out.append(f" {CLR_BOLD}WIFI-CSI HUMAN ACTIVITY RECOGNITION (BACKEND: {self.backend.upper()}){CLR_RESET}")
            out.append(f" Port: {self.port:<10} | Data Rate: {fps:>5.1f} Hz | Packets: {total}")
            out.append(f" Avg Amp: {recent_avg:>7.2f} | Activity Index: {activity_index:>7.4f}")
            out.append("="*80)
            
            # Prediction Highlight
            pred_color = CLR_FALL if pred.lower() == "fall" else CLR_GOOD
            out.append(f"\n CURRENT ACTIVITY: {pred_color}{CLR_BOLD}{pred.upper():<15}{CLR_RESET}")
            
            # Alert / Buffer Status
            if alert_active:
                out.append(f" {CLR_FALL}{CLR_BOLD}[!!!] {alert_msg} [!!!]{CLR_RESET}")
            elif pred.lower() == "waiting...":
                prog = min(buffer_count, window_size) / window_size
                bar_len = int(prog * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                out.append(f" Filling Buffer : [{bar}] {min(buffer_count, window_size)}/{window_size}")
            else:
                out.append("")
                
            out.append("-" * 80)
            
            # Probability Bars
            for cls, prob in zip(self.classes, probs):
                bar_len = int(prob * 45)
                bar = "█" * bar_len + "░" * (45 - bar_len)
                
                conf_thresh = getattr(settings, 'CONFIDENCE_THRESHOLD', 0.7)
                if prob > conf_thresh: color = CLR_FALL if cls == "fall" else CLR_GOOD
                elif prob > 0.3: color = CLR_INFO
                else: color = CLR_GREY
                    
                out.append(f" {cls:<10} | {color}{bar}{CLR_RESET} | {prob:>6.1%}")
            
            out.append("\n" + "="*80)
            model_disp = "final_har_model.keras" if self.backend == "keras" else "har_model_quantized.tflite"
            out.append(f" [CTRL+C] to Exit | Model: {model_disp}")
            
            sys.stdout.write("\n".join(out) + "\n")
            sys.stdout.flush()
            time.sleep(0.08)

    def start(self):
        self.is_running = True
        try:
            self.reader.start()
        except Exception as e:
            print(f"Error starting serial reader: {e}")
            return

        self.coll_thread = threading.Thread(target=self.data_collection_loop, daemon=True)
        self.inf_thread = threading.Thread(target=self.inference_loop, daemon=True)
        self.coll_thread.start()
        self.inf_thread.start()
        
        try:
            self.render_dashboard()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.is_running = False
        self.reader.stop()
        print("\nStopping Dashboard...")


# Running the inference dashboard
# python scripts/inference_dashboard.py --port COM3 --backend tflite

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live HAR Inference Dashboard")
    parser.add_argument("--port", type=str, default=settings.SERIAL_PORT)
    parser.add_argument("--backend", type=str, choices=["keras", "tflite"], default="keras", help="Inference Engine to execute (keras or tflite).")
    parser.add_argument("--model", type=str, default="", help="Optional override for exact model path.")
    parser.add_argument("--backend-url", type=str, default="https://fall-alert-backend-mdys.onrender.com/predictions")
    args = parser.parse_args()
    
    # Auto-resolve correct compiled model path intelligently based on user backend choice
    model_path = args.model
    if not model_path:
        if args.backend == "keras":
            # Prioritize legacy .h5 format (v7.0) for better portability
            h5_path = settings.MODEL_DIR / "final_har_model.h5"
            keras_path = settings.MODEL_DIR / "final_har_model.keras"
            model_path = str(h5_path if h5_path.exists() else keras_path)
        else:
            model_path = str(settings.MODEL_DIR / "har_model_quantized.tflite")
            
    if not os.path.exists(model_path):
        print(f"Error: Target model not found at {model_path}")
        print("Please run `train_final_model.py` (Keras) or `fast_export_tflite.py` (TFLite) first!")
        sys.exit(1)
        
    InferenceDashboard(args.port, model_path, backend=args.backend, backend_url=args.backend_url).start()

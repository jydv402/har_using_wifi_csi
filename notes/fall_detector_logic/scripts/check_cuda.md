# Textbook:
## 📦 Library Reference

### External Libraries
- **`tensorflow` (as `tf`)**: The target library being checked.
- **`tensorflow.python.platform.sysconfig`**: Specialized diagnostic tool.
    - **Usage**: Used to extract the system-level paths where TensorFlow expects to find the NVIDIA CUDA drivers.

### Local Dependencies
- **(None)**: This is an environment diagnostic script.

## 📖 Overview
AI math is too hard for a normal computer processor (CPU). The `check_cuda.py` script verifies that your computer has an NVIDIA GPU and that the drivers are correctly configured so your AI can run at "Turbo" speeds.
(via NVIDIA's CUDA). For a Wi-Fi sensing project running deep recurrent models (GRU), having GPU acceleration can significantly speed up training time.

---

## 💻 Code Walkthrough

### Verification logic
```python
1: import tensorflow as tf
2: from tensorflow.python.platform import sysconfig
4: cuda_lib_path = sysconfig.get_lib()
5: print("CUDA Library Path:", cuda_lib_path)
7: compile_flags = sysconfig.get_compile_flags()
8: print("Compile Flags:", compile_flags)
```

-   **Line 1**: Imports the `tensorflow` library.
-   **Line 2**: Imports `sysconfig` from `tensorflow.python.platform`. This module contains information about the build and environment configuration of the installed TensorFlow package.
-   **Line 4-5**: `sysconfig.get_lib()` retrieves the directory where the shared libraries (including those for CUDA, if enabled) are located. Printing this helps determine if TensorFlow is looking in the correct system path for the NVIDIA drivers.
-   **Line 7-8**: `sysconfig.get_compile_flags()` provides the flags used when building TensorFlow. This is useful for identifying if the version you have installed was compiled with `XLA` (Accelerated Linear Algebra) or `CUDA` support enabled.

---

---

## 🎓 Concept Deep-Dives

### 1. What are CUDA and cuDNN?
When TensorFlow runs on a CPU, it converts AI math into standard computer instructions.
- **CUDA**: Is a language created by NVIDIA that allows developers to talk directly to the GPU's thousands of tiny cores.
- **cuDNN**: Is a library of "Pre-solved" AI math problems optimized specifically for those cores.
- **The Result**: If this script returns "PASS", your training will be **10x to 50x faster** than on a standard laptop CPU.

---

## 🔗 Related Notes & Dependencies
- **Environment**: This is the first script you should run before starting the [train_model.md](file:///d:/Projects/major/notes/fall_detector_logic/scripts/train_model.md).
- **Configuration**: Relies on the TensorFlow installation detected by Python.

## 🎯 Key Takeaways
-   **Debugging Hardware**: If your model is training very slowly, running this script is the first step to see if TensorFlow is even "seeing" your GPU drivers.
-   **Compatibility**: This script helps verify that the versions of CUDA installed on your system match what TensorFlow expects.

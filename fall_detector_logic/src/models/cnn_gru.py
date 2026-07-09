import tensorflow as tf
from tensorflow.keras.layers import Conv1D, GRU, Dense, Dropout, BatchNormalization, Flatten, Input, GlobalAveragePooling1D
from config import settings
import numpy as np

def build_cnn_gru_model(input_shape, num_classes):
    """
    HAR v6.0 Model: Physcially Accurate Conv1D-GRU.
    Explicitly named layers to ensure load_weights(final_har_weights.h5) 
    works across all Keras versions.
    """
    inputs = Input(shape=input_shape, name="input_1")

    # Convolutional Feature Extraction
    x = Conv1D(64, kernel_size=3, padding='same', activation='relu', name="conv1")(inputs)
    x = BatchNormalization(name="bn1")(x)
    x = Conv1D(128, kernel_size=3, padding='same', activation='relu', name="conv2")(x)
    x = BatchNormalization(name="bn2")(x)
    
    # Recurrent Layer for Long-Term Activity
    x = GRU(128, return_sequences=True, dropout=0.2, name="gru1")(x)
    
    # Adaptive Pooling
    x = GlobalAveragePooling1D(name="gap1")(x)
    
    x = Dense(128, activation='relu', name="fc1")(x)
    x = Dropout(0.4, name="dropout1")(x)
    
    outputs = Dense(num_classes, activation='softmax', name="output_layer")(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="HAR_v6_Stable")

    # High-Recall focal loss for rare Fall events
    loss_fn = focal_loss_custom(num_classes=num_classes, gamma=2.5, alpha=0.5)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=settings.LEARNING_RATE),
        loss=loss_fn,
        metrics=['accuracy']
    )
    
    return model

def focal_loss_custom(num_classes, gamma=2.0, alpha=0.25):
    """
    Custom Focal Loss to handle extreme class imbalance (rare falls).
    """
    def focal_loss_fixed(y_true, y_pred):
        y_true = tf.cast(y_true, tf.int32)
        y_true_one_hot = tf.one_hot(tf.squeeze(y_true), depth=num_classes)
        
        epsilon = tf.keras.backend.epsilon()
        y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)
        cross_entropy = -y_true_one_hot * tf.math.log(y_pred)
        
        weight = alpha * tf.math.pow(1.0 - y_pred, gamma)
        loss = weight * cross_entropy
        
        return tf.reduce_mean(tf.reduce_sum(loss, axis=-1))
        
    return focal_loss_fixed

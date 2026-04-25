import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Lambda
from tensorflow.keras.optimizers import Adam

def arcface_loss(y_true, y_pred, m=0.5):
    cos_theta = tf.matmul(y_pred, tf.transpose(y_true))  # Compute cosine similarity
    theta = tf.acos(cos_theta)                         # Get angle between vectors
    adjusted_cos_theta = tf.cos(theta + m)             # Apply angular margin
    logits = adjusted_cos_theta                        # Convert back to logits
    loss = tf.keras.losses.categorical_crossentropy(y_true, logits)
    return loss

def build_arcface_model(input_shape, num_classes):
    inputs = Input(shape=input_shape)
    x = tf.keras.applications.ResNet50(include_top=False, weights=None)(inputs)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = Dense(units=num_classes)(x)
    outputs = Lambda(lambda x: tf.nn.l2_normalize(x, axis=1))(x)
    model = Model(inputs=inputs, outputs=outputs)
    return model

model = build_arcface_model((224, 224, 3), 1000)
model.compile(optimizer=Adam(), loss=lambda y_true, y_pred: arcface_loss(y_true, y_pred))

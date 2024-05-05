#!/usr/bin/env python3
# coding: utf-8
"""Voice command recoginization model trainer"""

import argparse
import json
import tensorflow as tf
import numpy as np
import audio_utils


def build_model2(input_shape, num_classes, train_ds):
    norm_layer = tf.keras.layers.Normalization()
    norm_layer.adapt(data=train_ds.map(map_func=lambda spec, label: spec))

    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=input_shape),
        # Downsample the input.
        tf.keras.layers.Resizing(32, 32),
        # Normalize.
        norm_layer,
        tf.keras.layers.Conv2D(32, 3, activation="relu"),
        tf.keras.layers.Conv2D(64, 3, activation="relu"),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Dropout(0.25),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(num_classes),
    ])

    return model


def build_model1(input_shape, num_classes, train_ds):
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(shape=input_shape),
        tf.keras.layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        tf.keras.layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
        tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
        tf.keras.layers.Dropout(0.25),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(num_classes, activation="softmax")
    ])
    return model


def load_dataset(data_dir,
                 sr=audio_utils.VOICE_SAMPLERATE,
                 duration=1.0,
                 batch_size=32,
                 feature="mfcc"):
    train_ds, val_ds = tf.keras.utils.audio_dataset_from_directory(
        directory=data_dir,
        validation_split=0.1,
        seed=0,
        batch_size=batch_size,
        output_sequence_length=sr * duration,
        subset="both")
    label_strs = train_ds.class_names

    mkfeature = lambda x: audio_utils.make_mfcc(x, sr=sr)
    if feature == "spectrogram":
        mkfeature = lambda x: audio_utils.make_spectrogram(x)

    def numpy_feature(audio_batch):
        # input data is (batch, x), so we have to loop the batch.
        a = audio_batch.numpy()
        sample_output = mkfeature(a[0])
        x, y = sample_output.shape
        output = np.zeros((a.shape[0], x, y))
        output[0] = sample_output
        for i in range(1, a.shape[0]):
            output[i] = mkfeature(a[i])
        output = np.expand_dims(output, axis=-1)
        return output

    def make_feature(audio, labels):
        audio = tf.squeeze(audio, axis=-1)
        features = tf.py_function(numpy_feature, [audio], Tout=tf.float32)
        return features, labels

    train_ds = train_ds.map(make_feature, tf.data.AUTOTUNE)
    val_ds = val_ds.map(make_feature, tf.data.AUTOTUNE)

    return (train_ds, val_ds, label_strs)


def train_voice_model(data_dir, model_fn, audio_sr, audio_duration, model_name,
                      epoches, batch_size, feature):
    train_ds, val_ds, label_strs = load_dataset(data_dir, audio_sr,
                                                audio_duration, batch_size,
                                                feature)
    for features, _ in train_ds.take(1):
        input_shape = features.shape[1:]
        batch_size = features.shape[0]
    cardinality = tf.data.experimental.cardinality(train_ds).numpy()
    if cardinality == tf.data.experimental.INFINITE_CARDINALITY:
        print(">>> The dataset is infinite")
    else:
        print(f">>> Total data batches in dataset: {cardinality}")
    print(f">>> Batch size: {batch_size}")
    print(f">>> Data labels: {label_strs}")
    print(f">>> Input shape: {input_shape}")
    print(f">>> Num of classes: {len(label_strs)}")
    if model_name == "v1":
        model = build_model1(input_shape, len(label_strs), train_ds)
    elif model_name == "v2":
        model = build_model2(input_shape, len(label_strs), train_ds)
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    print(model.summary())
    model.fit(train_ds, epochs=epoches)
    test_loss, test_accuracy = model.evaluate(val_ds)
    print(f">>> Test accuracy: {test_accuracy}, Test loss: {test_loss}")
    model.save(model_fn)
    with open(model_fn + ".labels", "w", encoding="utf8") as f:
        json.dump(label_strs, f, indent=2)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(model_fn + ".tflite", "wb") as f:
        f.write(tflite_model)
    print(f">>> Model saved to {model_fn}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", help="data directory")
    parser.add_argument("model_fn", help="file to save model into")
    parser.add_argument("--audio-sr",
                        default=audio_utils.VOICE_SAMPLERATE,
                        type=int,
                        help="audio clip sample rate")
    parser.add_argument("--audio-duration",
                        default=1.0,
                        type=float,
                        help="audio clip duration in secs.")
    parser.add_argument("--feature",
                        default="mfcc",
                        choices=("mfcc", "spectrogram"),
                        help="feature to extract (default: %(default)s)")
    parser.add_argument("--model",
                        default="v1",
                        choices=("v1", "v2"),
                        help="model to train (default: %(default)s)")
    parser.add_argument("--epoches",
                        default=50,
                        type=int,
                        help="training epoches")
    parser.add_argument("--batch-size",
                        default=32,
                        type=int,
                        help="batch size for training")
    args = parser.parse_args()
    train_voice_model(args.data_dir,
                      args.model_fn,
                      audio_sr=args.audio_sr,
                      audio_duration=args.audio_duration,
                      epoches=args.epoches,
                      batch_size=args.batch_size,
                      feature=args.feature,
                      model_name=args.model)


if __name__ == "__main__":
    main()

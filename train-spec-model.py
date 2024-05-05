#!/usr/bin/env python3
# coding: utf-8
"""Voice command recoginization model trainer"""

import argparse
import tensorflow as tf
import numpy as np
import json
import audio_utils


def build_model(input_shape, num_classes, train_ds):
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

    print(model.summary())
    return model


def load_dataset(data_dir: str) -> tf.data.Dataset:
    train_ds, val_ds = tf.keras.utils.audio_dataset_from_directory(
        directory=data_dir,
        batch_size=32,
        validation_split=0.1,
        seed=0,
        output_sequence_length=audio_utils.VOICE_SAMPLERATE * 1.5,
        subset="both")
    labels = train_ds.class_names

    def squeeze(audio, labels):
        audio = tf.squeeze(audio, axis=-1)
        return audio, labels

    train_ds = train_ds.map(squeeze, tf.data.AUTOTUNE)
    val_ds = val_ds.map(squeeze, tf.data.AUTOTUNE)

    return (train_ds, val_ds, labels)


def train_voice_model(data_dir, model_fn, epoches):
    train_ds, val_ds, label_strs = load_dataset(data_dir)

    def make_spec_ds(ds):
        return ds.map(map_func=lambda audio, label:
                      (audio_utils.make_spectrogram(audio), label),
                      num_parallel_calls=tf.data.AUTOTUNE)

    train_spec_ds = make_spec_ds(train_ds)
    val_spec_ds = make_spec_ds(val_ds)
    num_datapoints = train_spec_ds.reduce(0, lambda x, _: x + 1).numpy()
    print(f">>> Dataset contains {num_datapoints} data items " +
          f"with labels {label_strs}")
    for features, _ in train_spec_ds.take(1):
        input_shape = features.shape[1:]
    print(f">>> Input shape: {input_shape}")
    model = build_model(input_shape, len(label_strs), train_spec_ds)
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    model.fit(train_spec_ds, epochs=epoches)
    model.save(model_fn)
    with open(model_fn + ".labels", "w", encoding="utf8") as f:
        json.dump(label_strs, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_dir", help="data directory with files '<cmd>|<cmd>-cn/xxxx.wav'")
    parser.add_argument("model_fn", help="file to save model into")
    parser.add_argument("--epoches",
                        default=5,
                        type=int,
                        help="training epoches")
    args = parser.parse_args()
    train_voice_model(args.data_dir, args.model_fn, epoches=args.epoches)


if __name__ == "__main__":
    main()

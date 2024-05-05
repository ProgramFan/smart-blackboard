#!/usr/bin/env python3
# coding: utf-8
"""Voice command recoginization model trainer"""

import librosa
import argparse
import os
import tensorflow as tf
import numpy as np


def build_model(input_shape, num_classes):
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


def load_dataset(data_dir: str,
                 sr: int = 16000,
                 n_mfcc: int = 13) -> tf.data.Dataset:
    """
    Load audio files and their labels from the specified directory,
    compute the MFCCs, and return a TensorFlow Dataset containing the
    MFCCs and labels.

    Args:
        data_dir (str): The directory containing subdirectories of wav files.
        sr (int): The sample rate of the audio files.
        n_mfcc (int): The number of MFCCs to extract.

    Returns:
        tf.data.Dataset: A TensorFlow Dataset containing MFCCs and their labels.
    """

    all_labels = sorted(os.listdir(data_dir))
    label_to_int = {v: i for i, v in enumerate(all_labels)}

    labels = []
    features = []

    def preprocess(file_path):
        audio, _ = librosa.load(file_path, sr=sr)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
        label = label_to_int[file_path.split(os.sep)[-2]]
        mfcc = np.expand_dims(mfcc.T, axis=-1)
        mfcc = np.expand_dims(mfcc, axis=0)
        label = [label]
        return mfcc, [label]

    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".wav"):
                file_path = os.path.join(root, file)
                mfcc, label = preprocess(file_path)
                features.append(mfcc)
                labels.append(label)

    features = np.array(features)
    labels = np.array(labels)
    dataset = tf.data.Dataset.from_tensor_slices((features, labels))
    return dataset, all_labels


def train_voice_model(data_dir, model_fn):
    dataset, label_strs = load_dataset(data_dir)
    num_datapoints = dataset.reduce(0, lambda x, _: x + 1).numpy()
    print(f">>> Dataset contains {num_datapoints} data items " +
          f"with labels {label_strs}")
    for features, _ in dataset.take(1):
        input_shape = features.shape[1:]
    print(f">>> Input shape: {input_shape}")
    model = build_model(input_shape, len(label_strs))
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    model.fit(dataset, epochs=5)
    model.save(model_fn)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_dir", help="data directory with files '<cmd>|<cmd>-cn/xxxx.wav'")
    parser.add_argument("model_fn", help="file to save model into")
    args = parser.parse_args()
    train_voice_model(args.data_dir, args.model_fn)


if __name__ == "__main__":
    main()

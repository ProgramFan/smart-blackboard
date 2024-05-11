#!/usr/bin/env python3
# coding: utf-8
"""Voice command recoginization model trainer"""

import argparse
import json
import audio_utils
import numpy as np
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # disable tf console logging
# pylint: disable=wrong-import-position
import tensorflow as tf
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.models import Sequential


# Problem with this model: it does not converge in training, don't know why.
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
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

    return model


def create_model(name, input_shape, num_classes, dataset):
    if name == "v1":
        return build_model1(input_shape, num_classes, dataset)
    elif name == "v2":
        return build_model2(input_shape, num_classes, dataset)
    elif name == "v3":
        return Sequential([
            Conv2D(32, (3, 3), activation="relu", input_shape=input_shape),
            MaxPooling2D((2, 2)),
            Conv2D(64, (3, 3), activation="relu"),
            MaxPooling2D((2, 2)),
            Flatten(),
            Dense(64, activation="relu"),
            Dense(num_classes, activation="softmax")
        ])
    elif name == "v4":
        return Sequential([
            Flatten(input_shape=input_shape),
            Dense(128, activation="relu"),
            Dense(128, activation="relu"),
            Dense(num_classes, activation="softmax")
        ])

    else:
        return


def build_model1(input_shape, num_classes, _):
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
                 feature="mfcc",
                 **kwargs):
    """Load the audio files and convert them into a dataset of shape (batch,
    height, width, channel)"""
    train_ds, val_ds = tf.keras.utils.audio_dataset_from_directory(
        directory=data_dir,
        validation_split=0.1,
        seed=0,
        batch_size=1,  # use batch size 1 for easy datasize calc.
        output_sequence_length=sr * duration,
        subset="both")
    # first, we save all the label strings, since the dataset uses their indexes
    # as the labels.
    label_strs = train_ds.class_names

    def make_feature(data):
        if feature == "mfcc":
            return audio_utils.make_mfcc(data, sr=sr, **kwargs)
        else:
            return audio_utils.make_spectrogram(data)

    def make_dataset(ds):
        nitems = ds.cardinality().numpy()
        labels = np.zeros(nitems)
        for f, _ in ds.take(1):
            sample_feature = make_feature(f.numpy()[0, :, 0])
            shape = sample_feature.shape
            features = np.zeros((nitems, shape[0], shape[1]))
        for i, (f, l) in enumerate(ds):
            features[i] = make_feature(f.numpy()[0, :, 0])
            labels[i] = l.numpy()[0]
        features = np.expand_dims(features, axis=-1)  # add a last channel dim
        result = tf.data.Dataset.from_tensor_slices((features, labels))
        return result.batch(batch_size)

    train_ds = make_dataset(train_ds)
    val_ds = make_dataset(val_ds)

    return (train_ds, val_ds, label_strs)


def train_voice_model(data_dir, model_fn, audio_sr, audio_duration, model_name,
                      epoches, batch_size, feature, **kwargs):
    train_ds, val_ds, label_strs = load_dataset(data_dir, audio_sr,
                                                audio_duration, batch_size,
                                                feature, **kwargs)
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
    model = create_model(model_name, input_shape, len(label_strs), train_ds)
    model.compile(optimizer="adam",
                  loss="sparse_categorical_crossentropy",
                  metrics=["accuracy"])
    model.summary()
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
    parser.add_argument("--n_mfcc",
                        default=20,
                        type=int,
                        help="number of mfcc (only for mfcc feature)")
    parser.add_argument("--model",
                        default="v1",
                        choices=("v1", "v2", "v3", "v4"),
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
                      n_mfcc=args.n_mfcc,
                      model_name=args.model)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# coding: utf-8
"""Voice command recoginization model tester"""

import argparse
import tensorflow as tf
import numpy as np
import json
import audio_utils


def load_model(model_fn):
    model = tf.keras.models.load_model(model_fn)
    with open(model_fn + ".labels", encoding="utf-8") as f:
        label_strs = json.load(f)
    return (model, label_strs)


def do_predict(model_fn):
    dev_info = audio_utils.select_input_device()[0]
    model, label_strs = load_model(model_fn)
    try:
        while True:
            data = audio_utils.record_voice(dev_info[0], 1.5, dev_info[2])
            mfcc = audio_utils.make_spectrogram(data)
            predictions = model.predict(np.array([mfcc]))
            predictions = tf.nn.softmax(predictions)
            print("Probability:")
            for i, v in enumerate(predictions[0]):
                print(f"  {label_strs[i]}: {v*100:.3f}%")
            predicted_label_index = np.argmax(predictions, axis=1)[0]
            print(f"Voice command: {label_strs[predicted_label_index]}")
    except KeyboardInterrupt:
        return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_fn", help="file to load model from")
    args = parser.parse_args()
    do_predict(args.model_fn)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# coding: utf-8
"""Voice command recoginization model tester"""

import os
import librosa
import argparse
import re
import numpy as np
import json
import audio_utils
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # disable tf console logging
import tensorflow as tf  # pylint: disable=wrong-import-position


def load_model(model_fn):
    model = tf.keras.models.load_model(model_fn)
    with open(model_fn + ".labels", encoding="utf-8") as f:
        label_strs = json.load(f)
    return (model, label_strs)


def do_predict(model_fn, sr, duration, feature="mfcc", **kwargs):
    dev_infos = audio_utils.select_input_device()
    print("Input devices on system: ")
    for i, v in enumerate(dev_infos):
        print(f"  [{i}] {v}")
    while True:
        chosen = input(f"Which device to use ? [0-{len(dev_infos)-1}]: ")
        if not re.match(r"^\d+$", chosen):
            continue
        chosen = int(chosen)
        if chosen < 0 or chosen >= len(dev_infos):
            continue
        break
    dev_info = dev_infos[chosen]
    model, label_strs = load_model(model_fn)

    def mkfeature(x):
        if feature == "spectrogram":
            return audio_utils.make_spectrogram(x)
        else:
            return audio_utils.make_mfcc(x, sr=sr, **kwargs)

    try:
        while True:
            data = audio_utils.record_voice(dev_info[0],
                                            duration,
                                            dev_info[2],
                                            downsample=False)
            if dev_info[2] != sr:
                data = librosa.resample(data,
                                        orig_sr=dev_info[2],
                                        target_sr=sr)
            indata = mkfeature(data)
            indata = np.expand_dims(indata, axis=-1)  # add extra channel
            predictions = model.predict(np.array([indata]))[0]
            print("Probability:")
            for i, v in enumerate(predictions):
                print(f"  {label_strs[i]}: {v*100:.3f}%")
            predicted_label_index = np.argmax(predictions)
            print(f"Voice command: {label_strs[predicted_label_index]}")
            for i in range(5):
                print(f"{5-i} ", end="", flush=True)
                time.sleep(0.8)
            print("=>", flush=True)
    except KeyboardInterrupt:
        return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_fn", help="pretrained model file")
    parser.add_argument("--sr",
                        type=int,
                        default=audio_utils.VOICE_SAMPLERATE,
                        help="voice sample rate (shall match training data)")
    parser.add_argument("--duration",
                        type=float,
                        default=1.5,
                        help="voice record secs (shall match training data)")
    parser.add_argument("--feature",
                        default="mfcc",
                        choices=("mfcc", "spectrogram"),
                        help="feature to extract (default: %(default)s)")
    parser.add_argument("--n_mfcc",
                        default=20,
                        type=int,
                        help="number of mfcc (only for mfcc feature)")
    args = parser.parse_args()
    do_predict(args.model_fn,
               args.sr,
               args.duration,
               args.feature,
               n_mfcc=args.n_mfcc)


if __name__ == "__main__":
    main()

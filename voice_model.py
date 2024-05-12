#!/usr/bin/env python3
# coding: utf-8
"""Voice command model"""

import librosa
import numpy as np
import json
import audio_utils
import argparse
import time
import re

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite


class VoiceCmdModel(object):
    """A voice command predication model based on mfcc"""

    def __init__(self, fn, sr, duration, feature, **kwargs):
        self.model = tflite.Interpreter(model_path=fn + ".tflite")
        self.model.allocate_tensors()
        self.input_details = self.model.get_input_details()
        self.output_details = self.model.get_output_details()
        with open(fn + ".labels", encoding="utf-8") as f:
            self.label_strs = json.load(f)
        self.model_sr = sr
        self.model_duration = duration
        self.model_feature = feature
        self.model_args = kwargs

    def make_feature(self, voice):
        if self.model_feature == "mfcc":
            return audio_utils.make_mfcc(voice,
                                         sr=self.model_sr,
                                         **self.model_args)
        elif self.model_feature == "spectrogram":
            return audio_utils.make_spectrogram(voice, **self.model_args)
        else:
            raise ValueError(f"Bad model feature {self.model_feature}")

    def predict(self, voice, sr):
        # preprocess the voice data to match the original model sr and length
        if sr != self.model_sr:
            voice = librosa.resample(voice,
                                     orig_sr=sr,
                                     target_sr=self.model_sr)
        n_datapoints = int(self.model_sr * self.model_duration)
        voice = np.pad(voice[:n_datapoints],
                       (0, max(0, n_datapoints - len(voice))),
                       "constant",
                       constant_values=(0.0, ))
        feature = self.make_feature(voice)
        feature = np.expand_dims(feature, axis=-1)  # add extra channel

        self.model.set_tensor(self.input_details[0]["index"],
                              np.array([feature], dtype=np.float32))
        self.model.invoke()  # Run inference
        predictions = self.model.get_tensor(self.output_details[0]["index"])[0]

        probability = dict(zip(self.label_strs, predictions))
        predicted_label = self.label_strs[np.argmax(predictions)]
        return {"command": predicted_label, "details": probability}


def loop_predict(model_fn, sr, duration, feature, **kwargs):
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

    model = VoiceCmdModel(model_fn, sr, duration, feature, **kwargs)
    try:
        while True:
            data = audio_utils.record_voice(dev_info[0],
                                            duration,
                                            dev_info[2],
                                            downsample=False)
            result = model.predict(data, dev_info[2])
            print(f"Voice command: {result['command']}")
            print("Probability:")
            for k, v in result["details"].items():
                print(f"  {k}: {v*100:.3f}%")
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
    loop_predict(args.model_fn,
                 args.sr,
                 args.duration,
                 args.feature,
                 n_mfcc=args.n_mfcc)


if __name__ == "__main__":
    main()

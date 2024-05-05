#!/usr/bin/env python3
# coding: utf-8
"""Helpers to support voice recording."""

import librosa
import sounddevice as sd
import numpy as np
import scipy
import os
import re

VOICE_SAMPLERATE = 16000


def select_sample_rate(dev):
    rates_to_test = [16000, 32000, 44100, 48000, 96000, 128000]
    supported_rates = []
    for rate in rates_to_test:
        try:
            sd.check_input_settings(samplerate=rate, device=dev)
            supported_rates.append(rate)
        except sd.PortAudioError:
            pass
    return min(supported_rates) if supported_rates else None


def select_input_device():
    result = []
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] == 0:
            continue
        if dev["max_output_channels"] != 0:
            continue
        sample_rate = select_sample_rate(i)
        if sample_rate is None:
            continue
        result.append((i, dev["max_input_channels"], sample_rate))
    return result


def record_voice(dev, duration, samplerate, downsample=True):
    rec = sd.rec(int(duration * samplerate),
                 samplerate=samplerate,
                 channels=1,
                 dtype="float32",
                 device=dev)
    sd.wait()
    rec = rec.flatten()
    if downsample and samplerate > VOICE_SAMPLERATE:
        rec = librosa.resample(rec,
                               orig_sr=samplerate,
                               target_sr=VOICE_SAMPLERATE)
    return rec


def save_voice(data, fn):
    scipy.io.wavfile.write(fn, VOICE_SAMPLERATE, np.int16(data * 32767))


def extract_voice_features(audio, feature="mfcc", **kwargs):
    if feature == "mfcc":
        return make_mfcc(audio, **kwargs)
    elif feature == "spectrogram":
        return make_spectrogram(audio, **kwargs)
    else:
        raise ValueError(f"Invalid voice feature {feature!r}")


def make_mfcc(audio_array, sr=VOICE_SAMPLERATE, n_mfcc=13):
    """Convert 1d audio to 2d image using mfcc"""
    mfcc = librosa.feature.mfcc(y=audio_array, sr=sr, n_mfcc=n_mfcc)
    return mfcc.T  # first dim is time, the second is mfcc


def make_spectrogram(audio_array, n_fft=2048, hop_length=512):
    """Convert 1d audio to 2d image using spectrogram"""
    d = librosa.stft(audio_array, n_fft=n_fft, hop_length=hop_length)
    d = librosa.amplitude_to_db(np.abs(d), ref=np.max(np.abs(d)))
    return d


def draw_spectrogram(ax, data, samplerate, title=True, xlabel=True):
    n_fft = 2048
    hop_length = 512
    d = librosa.stft(data, n_fft=n_fft, hop_length=hop_length)
    d = librosa.amplitude_to_db(np.abs(d), ref=np.max(np.abs(d)))
    ax.clear()
    t_max = len(data) / samplerate
    f_max = samplerate / 2
    extent = [0, t_max, 0, f_max]
    ax.imshow(d, aspect="auto", origin="lower", cmap="cool", extent=extent)
    if title:
        ax.set_title("Spectrogram")
    if xlabel:
        ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")


def draw_waveform(ax, data, samplerate, title=True, xlabel=True):
    num_samples = len(data)
    duration = num_samples / samplerate
    time = np.linspace(0, duration, num_samples, endpoint=False)
    ax.clear()
    ax.plot(time, data)
    if title:
        ax.set_title("Raw Waveform")
    if xlabel:
        ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Amplitude")


def make_filename(outdir):
    ids = []
    for fn in os.listdir(outdir):
        if re.match(r"\d+\.wav", fn):
            ids.append(int(os.path.splitext(fn)[0]))
    fid = 0
    if ids:
        ids.sort()
        for i in range(len(ids)):
            if ids[i] != i:
                fid = i
                break
        else:
            fid = ids[-1] + 1
    return os.path.join(outdir, f"{fid:04d}.wav")


def test():
    dev = select_input_device()
    if not dev:
        print("ERROR: No proper audio input is found!")
        return
    dev = dev[0]
    print(f"Recording on device {dev[0]} with samplerate {dev[2]}")
    rec = record_voice(dev[0], 1, dev[2])
    outfn = "test.wav"
    print(f"Write to {outfn}")
    save_voice(outfn, rec)


if __name__ == "__main__":
    test()

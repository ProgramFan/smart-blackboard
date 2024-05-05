#!/usr/bin/env python3
# coding: utf-8
"""A simple tool to record audio clips."""

import argparse
import tkinter as tk
import tkinter.font as tkFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
import audio_utils


class AudioRecorderApp:
    """A simple app to record audio into wav file"""

    def __init__(self, master, duration, outdir, scale=1.0):
        self.master = master
        master.title("Audio Recorder")

        dpi = int(96 * scale)
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, dpi=dpi)
        self.canvas = FigureCanvas(self.figure, master=master)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.record_button = tk.Button(master,
                                       text="Record Audio",
                                       command=self.record_and_plot)
        self.record_button.pack()

        self.save_button = tk.Button(master,
                                     text="Save Audio",
                                     command=self.save_audio)
        self.save_button.pack()

        self.input_dev_info = audio_utils.select_input_device()[0]
        self.audio_data = None
        self.input_dev = self.input_dev_info[0]
        self.recording_rate = self.input_dev_info[2]
        self.duration = duration
        self.outdir = outdir

    def record_and_plot(self):
        """Record audio and plot the spectrogram and waveform."""
        self.audio_data = audio_utils.record_voice(self.input_dev,
                                                   self.duration,
                                                   self.recording_rate)
        audio_utils.draw_waveform(self.ax1,
                                  self.audio_data,
                                  audio_utils.VOICE_SAMPLERATE,
                                  title=False,
                                  xlabel=False)
        audio_utils.draw_spectrogram(self.ax2,
                                     self.audio_data,
                                     audio_utils.VOICE_SAMPLERATE,
                                     title=False)
        self.canvas.draw()

    def save_audio(self):
        """Save the recorded audio data to a file."""
        if self.audio_data is None:
            print("No audio data to save.")
            return
        outfn = audio_utils.make_filename(self.outdir)
        audio_utils.save_voice(self.audio_data, outfn)
        print(f"Audio data saved to {outfn}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("duration",
                        type=float,
                        help="audio clip duration in secs.")
    parser.add_argument("outdir", help="output dir")
    parser.add_argument("--ui-scale-factor",
                        type=float,
                        default=1.0,
                        help="UI scaling factor (default: 1.0)")
    args = parser.parse_args()

    root = tk.Tk()
    if args.ui_scale_factor > 1.0:
        scale = args.ui_scale_factor
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(size=int(default_font.cget("size") * scale))
        text_font = tkFont.nametofont("TkTextFont")
        text_font.configure(size=int(text_font.cget("size") * scale))
    _ = AudioRecorderApp(root,
                         args.duration,
                         args.outdir,
                         scale=args.ui_scale_factor)
    root.mainloop()


if __name__ == "__main__":
    main()

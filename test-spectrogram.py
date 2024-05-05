# coding: utf-8
import ts
import tensorflow as tf
ds0, ds1 = tf.keras.utils.audio_dataset_from_directory(directory="data", validation_split=0.1, seed=0, output_sequence_length=48000*1.5, subset="both")
ds0.class_names
ds0.element_spec
def squeeze(audio, labels):
    return tf.squeeze(audio, axis=-1), labels
    
ds0 = ds0.map(squeeze, tf.data.AUTOTUNE)
ds1 = ds1.map(squeeze, tf.data.AUTOTUNE)
ds0.element_spec
for features, labels in ds0.take(1):
    print(features.shape)
    print(labels.shape)
    
def get_spectrogram(wf):
    result = tf.signal.stft(wf, frame_length=255, frame_step=128)
    result = tf.abs(result)
    result = result[..., tf.newaxis]
    return result
    
def make_spec_ds(ds):
    return ds.map(map_func=lambda a, l: (get_spectrogram(a), l))
    
ds0_spec = make_spec_ds(ds0)
ds1_spec = make_spec_ds(ds1)

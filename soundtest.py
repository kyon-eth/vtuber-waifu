import sounddevice as sd
import numpy as np
import wave
import threading
import time

def play_to_virtual_mic(wave_file_path, device_index):
    
    try:
        with wave.open(wave_file_path, 'rb') as wf:
            samplerate = wf.getframerate()
            channels = wf.getnchannels()

            # Read all frames from the wave file
            frames = wf.readframes(-1)
            audio_data = np.frombuffer(frames, dtype=np.int16)
            
            with sd.OutputStream(device=device_index, channels=channels, samplerate=samplerate, dtype='int16') as stream:
                stream.write(audio_data)

    except Exception as e:
        print(f"An error occurred: {e}")

# Define the range of device indices you want to use
device_indices_range = range(5, 10)  # Replace with the range you prefer

while True:
    for device_index in device_indices_range:
        print(f"Playing sound to device index: {device_index}")
        play_to_virtual_mic("test.wav", device_index)
        print("...played")
        time.sleep(2)

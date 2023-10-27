import sounddevice as sd
import numpy as np
import wave
import threading
import time

VIRTUAL_MIC_DEVICE_INDEX = 2  # Replace with your virtual microphone index

def play_to_virtual_mic(wave_file_path):
    
    def stream_audio():
        try:
            with wave.open(wave_file_path, 'rb') as wf:
                samplerate = wf.getframerate()
                channels = wf.getnchannels()

                # Read all frames from the wave file
                frames = wf.readframes(-1)
                audio_data = np.frombuffer(frames, dtype=np.int16)
                
                with sd.OutputStream(device=VIRTUAL_MIC_DEVICE_INDEX, channels=channels, samplerate=samplerate, dtype='int16') as stream:
                    stream.write(audio_data)

        except Exception as e:
            print(f"An error occurred: {e}")

    # Run the streaming in a separate thread
    threading.Thread(target=stream_audio).start()
    
    
while True:
    play_to_virtual_mic("output.wav")
    time.sleep(2)
    
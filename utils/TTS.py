import os
import torch
import requests
import urllib.parse
import datetime
import soundfile as sf
# from utils.katakana import *

# https://github.com/snakers4/silero-models#text-to-speech
def silero_tts(tts, language, model, speaker):
    # device = torch.device('gpu' if torch.cuda.is_available() else 'cpu')
    try:
        device = 'cpu'
        torch.set_num_threads(4)
        local_file = 'model.pt'

        if not os.path.isfile(local_file):
            torch.hub.download_url_to_file(f'https://models.silero.ai/models/tts/{language}/{model}.pt',
                                        local_file)  

        model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
        model.to(device)

        sample_rate = 48000

        audio = model.apply_tts(text=tts,
                                speaker=speaker,
                                sample_rate=sample_rate)
        
        # Generating a unique filename using timestamp
        filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + '.wav'
        filepath = os.path.join('output_audios', filename)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save the audio file
        sf.write(filepath, audio, sample_rate)
        
        return filepath
    except:
        return None
    
def voicevox_tts(tts):
    # You need to run VoicevoxEngine.exe first before running this script
    
    voicevox_url = 'http://localhost:50021'
    # Convert the text to katakana. Example: ORANGE -> オレンジ, so the voice will sound more natural
    # katakana_text = katakana_converter(tts)
    katakana_text = tts
    # You can change the voice to your liking. You can find the list of voices on speaker.json
    # or check the website https://voicevox.hiroshiba.jp
    params_encoded = urllib.parse.urlencode({'text': katakana_text, 'speaker': 46})
    request = requests.post(f'{voicevox_url}/audio_query?{params_encoded}')
    params_encoded = urllib.parse.urlencode({'speaker': 46, 'enable_interrogative_upspeak': True})
    request = requests.post(f'{voicevox_url}/synthesis?{params_encoded}', json=request.json())

    with open("test.wav", "wb") as outfile:
        outfile.write(request.content)

if __name__ == "__main__":
    silero_tts()

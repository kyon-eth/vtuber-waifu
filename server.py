import asyncio
import random
import websockets
from rich.logging import RichHandler
import logging
import openai
import json
import sounddevice as sd
import numpy as np
import wave
import threading
from config import *
from utils.TTS import *
from utils.subtitle import *
from utils.promptMaker import *

# import logging.config
# logging.config.dictConfig({
#     'version': 1,
#     'disable_existing_loggers': True
# })

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("waifuserver")

openai.api_key = api_key

conversation = []
history = {"history": conversation}

mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Ardha"
blacklist = ["Nightbot", "streamelements"]

queue_recv = asyncio.Queue()  
queue_proc = asyncio.Queue(maxsize=1)

# Global variable to store speaking duration
speak_duration = 0

def get_openai_response(prompt):
    try:
        # Creating a chat completion with the user's prompt
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
        )
        
        # Extracting the assistant’s reply from the response
        message = response['choices'][0]['message']['content']
        return message
    
    except Exception as e:
        print(f"An error occurred while querying the OpenAI API: {e}")
        return None

# function to get an answer from OpenAI
def openai_answer():
    global total_characters, conversation
    
    try:

        total_characters = sum(len(d['content']) for d in conversation)

        while total_characters > 4000:
            try:
                logging.info("total characters: {0}".format(total_characters))
                logging.info("len conversation: {0}".format(len(conversation)))
                conversation.pop(2)
                total_characters = sum(len(d['content']) for d in conversation)
            except Exception as e:
                logging.info("Error removing old messages: {0}".format(e))

        with open("conversation.json", "w", encoding="utf-8") as f:
            # Write the message data to the file in JSON format
            json.dump(history, f, indent=4)

        prompt = getPrompt()

        message = get_openai_response(prompt)
        
        logging.info("Response: {0}".format(message))
        conversation.append({'role': 'assistant', 'content': message})

        if ":" in message:
            message = message.split(":")[1]
            message = message.strip()

        if message == "":
            return None
        else:
            return silero_tts(message, "en", "v3_en", "en_21")

    except:
        return None


def play_to_virtual_mic(wave_file_path, text):
    
    def stream_audio():
        try:
            global speak_duration
            # Generate Subtitle
            generate_subtitle(chat_now, text)

            with wave.open(wave_file_path, 'rb') as wf:
                samplerate = wf.getframerate()
                channels = wf.getnchannels()

                # Read all frames from the wave file
                frames = wf.readframes(-1)
                audio_data = np.frombuffer(frames, dtype=np.int16)
                
                with sd.OutputStream(device=VIRTUAL_MIC_DEVICE_INDEX, channels=channels, samplerate=samplerate, dtype='int16') as stream:
                    stream.write(audio_data)
                    
                os.remove(wave_file_path)
        
                with open ("output.txt", "w") as f:
                    f.truncate(0)
                with open ("chat.txt", "w") as f:
                    f.truncate(0)
                    
                speak_duration = 0

        except Exception as e:
            print(f"An error occurred: {e}")

    threading.Thread(target=stream_audio).start()

def preparation(chat):
    global conversation, chat_now, chat_prev
    chat_now = chat
    if chat_now != chat_prev:
        logging.info("chat now: {0}".format(chat_now))
        # Saving chat history
        conversation.append({'role': 'user', 'content': chat_now})
        chat_prev = chat_now
        return openai_answer()
    else:
        return None

async def preprocess_message(queue_recv, queue_proc):
    global speak_duration
    while True:
        message = await queue_recv.get()  
        logging.info(f"Preprocessing: {message}")
        
        # Wait for a duration based on speaking duration
        if speak_duration:
            logging.info(f"Speaking pause: {speak_duration}s")
        
            # Skip some messages received during speaking duration
            skipped_messages = []
            while not queue_recv.empty():
                skipped_messages.append(await queue_recv.get())
            
            if skipped_messages:  
                # get last message
                logging.info(f"Skipped messages: {len(skipped_messages)} - 1")
                message = skipped_messages[-1]
                
            await asyncio.sleep(speak_duration)
        
        # (Your preprocessing code here, such as openai_answer(), etc.)
        audio = preparation(message)  
        await queue_proc.put({"audio": audio, 
                              "message": message,}) 
        logging.info(f"Preprocessed: {message}")
        
        
async def handle_message(queue_proc):
    while True:
        global speak_duration
        data = await queue_proc.get()
        
        audio_file, message = data["audio"], data["message"]
        
        if audio_file:
            with wave.open(audio_file, 'rb') as wf:
                speak_duration = wf.getnframes() / wf.getframerate()
            
            play_to_virtual_mic(audio_file, message)
            
            logging.info(f"Handled: {message}")
        else:
            logging.error(f"Error: {message}")


async def echo(websocket, path, queue_recv):
    async for message in websocket:
        logging.info(f"Received: {message}")
        await queue_recv.put(message)


async def main():
    asyncio.create_task(preprocess_message(queue_recv, queue_proc))
    asyncio.create_task(handle_message(queue_proc)) 
    
    start_server = await websockets.serve(lambda ws, path: echo(ws, path, queue_recv), "localhost", 8765)
    
    await start_server.wait_closed()

asyncio.run(main())
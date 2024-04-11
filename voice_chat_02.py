import os
import io
import requests
import audioop
import pyaudio
import wave
from playsound import playsound
import numpy as np
from dotenv import load_dotenv

import pvporcupine
import openai
from google.cloud import speech

from utils.audio_utils import listener, record_wav, speech_to_text, text_to_speech


load_dotenv()

# Load API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
pvpkey = os.getenv("PICO_VOICE_KEY")
access_key = f"{pvpkey}"

# Wake word and sleep word
wakeword = ['wakeword\Hey-Judy_en_windows_v3_0_0.ppn']
sleep_word = "exit"

#initialize the wakeword detection
handle = pvporcupine.create(access_key=access_key, keyword_paths=wakeword)

gpt_response = ""

delimiter = "####"

AGENT_CONTEXT="""
You a conversation bot.
When approriate ask questions at the end of responses to keep the conversation going. 
Keep answers short--only 3-4 sentences max.
"""

# Voices to choose from, Nicole, Arjun, Knightley, Natasha, Lily, Jeremy
ELEVENLABS_VOICE_NAME = "Knightley"

def main():

    listener(handle)

    messages=[
      {"role": "system", "content": AGENT_CONTEXT},
      # {"role": "assistant", "content":""}
      # {"role": "function", "content":""}
      ]
    
    count = 0
    response_count = 0
    
    while True:

        # Get WAV from microphone.
        record_wav()

        # Convert audio into text.
        question = speech_to_text("input.wav")

        if sleep_word in question.lower():
            break

        messages.append({'role':'user', 'content':f"{delimiter} + {question} + {delimiter}"})

        # Send text to ChatGPT.
        print(f"Asking: {question}")
        response, usage = get_completion(messages)

        messages.append({"role": "assistant", "content":f"{response}"})

        print(usage)
        print(response + "\n")

        # Convert ChatGPT response into audio.
        text_to_speech(response, response_count, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME)

        playsound(f"response/result{response_count}.mp3")
        
        response_count += 1
        count += 1
        if count > 2:
            break
        else:
            continue
        

def get_completion(messages, model="gpt-4", temperature=0,max_tokens=2000):

  response = openai.ChatCompletion.create(
    model=model,
    temperature=temperature,
    max_tokens=max_tokens,
    messages=messages
  )
  usage = response["usage"]
  return response.choices[0].message.content, usage



if __name__ == "__main__":
    main()

import os
from playsound import playsound
from dotenv import load_dotenv
import sys

import pvporcupine
import openai
from langchain.tools.render import format_tool_to_openai_function

from utils.audio_utils import listener, record_wav, speech_to_text, text_to_speech, close_stream
from utils.bot_tools import get_current_temperature, lights_on, search_wikipedia, scrape_news
from agent_model import v_agent


load_dotenv()

# Load API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
pvpkey = os.getenv("PICO_VOICE_KEY")
access_key = f"{pvpkey}"

# Wake word and sleep word
wakeword = ['wakeword\Hey-Judy_en_windows_v3_0_0.ppn']
SLEEP_WORD = "exit"
SHUT_DOWN = "shut down"

#initialize the wakeword detection
handle = pvporcupine.create(access_key=access_key, keyword_paths=wakeword)

delimiter = "####"

AGENT_CONTEXT="""
You are a sassy bot which can converse or use specific tools. 
If a question is asked which uses a tool, don't assume--ask clarifying questions where needed.
When approriate ask questions at the end of responses to keep the conversation going.
Keep answers short--only 3-4 sentences max.
"""

# Voices to choose from, Nicole, Arjun, Knightley, Natasha, Lily, Jeremy
ELEVENLABS_VOICE_NAME = "Lily"

tools = [get_current_temperature, lights_on, search_wikipedia, scrape_news]
functions = [format_tool_to_openai_function(f) for f in tools]

def main(tools):

    while True:
      stream, audio = listener(handle)
      
      count = 0
      response_count = 0
      playsound("sounds/confirm.wav")

      while True:
          # Get WAV from microphone.
          record_wav(stream, audio)

          # Convert audio into text.
          question = speech_to_text("input.wav")

          if SLEEP_WORD in question.lower():
              playsound("sounds/tone.wav")
              break
          if SHUT_DOWN in question.lower():
              playsound("sounds/power_down.mp3")
              sys.exit()

          # Send text to ChatGPT.
          print(f"Asking: {question}")

          cb = v_agent(tools, AGENT_CONTEXT)

          response = cb.convchain(question)

          print(response)

          #text_to_speech(response, response_count, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME)

          #playsound(f"response/result{response_count}.mp3")
          
          response_count += 1
          count += 1
          if count > 2:
              break
          else:
              continue
      
      close_stream(stream, audio)


if __name__ == "__main__":
    main(tools)
import os
from playsound import playsound
from dotenv import load_dotenv
import json
import time

import pvporcupine
from langchain_core.utils.function_calling import convert_to_openai_function

from utils.audio_utils import listener, speech_to_text, text_to_speech, close_stream
from utils.bot_tools import get_current_temperature, lights_on, search_wikipedia, scrape_news
from utils.agent_model import Assistant

load_dotenv()


# Load API keys
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
pvpkey = os.getenv("PICO_VOICE_KEY")
access_key = f"{pvpkey}"

# Wake word and sleep word
wakeword = ['wakeword\hey-steven_en_windows_v3_0_0.ppn']
SLEEP_WORD = "exit"
SHUT_DOWN = "shut down"

# option to allow you to switch between different model APIs
# Options include: "get_openai_completion", "anthropic", "google"
agent_api="get_openai_completion"

#initialize the wakeword detection
handle = pvporcupine.create(access_key=access_key, keyword_paths=wakeword)

delimiter = "####"

AGENT_CONTEXT="""
Your name is Stephen. You are a bot which can converse or use specific tools. 
If a question is asked which uses a tool, don't assume--ask clarifying questions where needed.
When approriate ask questions at the end of responses to keep the conversation going. 
Keep answers short--only 3-4 sentences max.
"""

# Voices to choose from, Nicole, Arjun, Knightley, Natasha, Lily, Jeremy
ELEVENLABS_VOICE_NAME = "Stephen_G"

tools = [get_current_temperature, lights_on, search_wikipedia, scrape_news]
functions = [convert_to_openai_function(f) for f in tools]

def main(tools):
    
    messages=[
    {"role": "system", "content": AGENT_CONTEXT},
    # {"role": "assistant", "content":""}
    # {"role": "function", "content":""}
    ]

    listener(handle)
    
    count = 0
    response_count = 0

    while True:
        # tracking response time
        resp_start = time.time() 

        # Convert audio into text.
        question = speech_to_text()

        if SLEEP_WORD in question.lower():
            playsound("sounds/confirm.wav")
            break

        messages.append({'role':'user', 'content':f"{delimiter} + {question} + {delimiter}"})

        # Send text to ChatGPT.
        print(f"Asking: {question}")
        response = getattr(Assistant, agent_api)(messages, functions)

        print("Response Recieved")
        print(response)
        if response.function_call:
          tools = tools
          function_name = response.function_call.name
          func_to_call = next(filter(lambda x: x.name == function_name, tools), None)
          args = json.loads(response.function_call.arguments)
          print(args)
          func_response = func_to_call(args)
          messages.append({"role": "function", "name": function_name, "content": func_response})
          function_return = getattr(Assistant, agent_api)(messages, functions)
          text_to_speech(function_return.content, response_count, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME)
          print(function_return.content + "\n")
        
        else:
          content = response.content
          messages.append({"role": "assistant", "content":f"{content}"})
          text_to_speech(content, response_count, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME)
          print(content + "\n")

        # Printing response time for the voice assistant
        resp_end = time.time()
        print(f"Total response time: {resp_end - resp_start}")

        # Convert ChatGPT response into audio.
        playsound(f"response/result{response_count}.mp3")
        

if __name__ == "__main__":
    main(tools)
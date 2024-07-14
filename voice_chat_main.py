import os
from playsound import playsound
from dotenv import load_dotenv
import json

import pvporcupine
from openai import OpenAI
from langchain_core.utils.function_calling import convert_to_openai_function

from utils.audio_utils import listener, record_wav, speech_to_text, text_to_speech, close_stream
from utils.bot_tools import get_current_temperature, lights_on, search_wikipedia, scrape_news

load_dotenv()

# Load API keys
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
pvpkey = os.getenv("PICO_VOICE_KEY")
access_key = f"{pvpkey}"

client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY"),  # this is also the default, it can be omitted
)

# Wake word and sleep word
wakeword = ['wakeword\hey-steven_en_windows_v3_0_0.ppn']
SLEEP_WORD = "exit"
SHUT_DOWN = "shut down"

#initialize the wakeword detection
handle = pvporcupine.create(access_key=access_key, keyword_paths=wakeword)

delimiter = "####"

AGENT_CONTEXT="""
You a use a bot which can converse or use specific tools. 
If a question is asked which uses a tool, don't assume--ask clarifying questions where needed.
When approriate ask questions at the end of responses to keep the conversation going. 
Keep answers short--only 3-4 sentences max.
"""

# Voices to choose from, Nicole, Arjun, Knightley, Natasha, Lily, Jeremy
ELEVENLABS_VOICE_NAME = "Stephen_G"

tools = [get_current_temperature, lights_on, search_wikipedia, scrape_news]
functions = [convert_to_openai_function(f) for f in tools]

def main(tools):

    listener(handle)

    messages=[
      {"role": "system", "content": AGENT_CONTEXT},
      # {"role": "assistant", "content":""}
      # {"role": "function", "content":""}
      ]
    
    count = 0
    response_count = 0

    while True:
        # # Get WAV from microphone.
        # record_wav(stream, audio)

        # Convert audio into text.
        question = speech_to_text()

        if SLEEP_WORD in question.lower():
            playsound("sounds/confirm.wav")
            break

        messages.append({'role':'user', 'content':f"{delimiter} + {question} + {delimiter}"})

        # Send text to ChatGPT.
        print(f"Asking: {question}")
        response = get_completion(messages)

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
          function_return = get_completion(messages)
          text_to_speech(function_return.content, response_count, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME)
          print(function_return.content + "\n")
        
        else:
          content = response.content
          messages.append({"role": "assistant", "content":f"{content}"})
          text_to_speech(content, response_count, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME)
          print(content + "\n")

        # Convert ChatGPT response into audio.
        playsound(f"response/result{response_count}.mp3")
        
        response_count += 1
        count += 1
        if count > 2:
            break
        else:
            continue
    
    close_stream(stream, audio)

def get_completion(messages, model="gpt-4", temperature=0,max_tokens=2000):

  response = client.chat.completions.create(
    model=model,
    temperature=temperature,
    max_tokens=max_tokens,
    messages=messages,
    functions=functions
  )
  return response.choices[0].message

if __name__ == "__main__":
    main(tools)
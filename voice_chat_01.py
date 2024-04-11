import os
import io
import sys
import asyncio
import audioop
import pyaudio
import wave
from google.cloud import speech
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

gpt_response = ""

delimiter = "####"

AGENT_CONTEXT="""
You a conversation bot.
When approriate ask questions at the end of responses to keep the conversation going. 
Keep answers short--only 3-4 sentences max.
"""

def main():

    messages=[
      {"role": "system", "content": AGENT_CONTEXT},
      # {"role": "assistant", "content":""}
      # {"role": "function", "content":""}
      ]
    
    count = 0

    while True:

        # Get WAV from microphone.
        record_wav()

        # Convert audio into text.
        question = speech_to_text("input.wav")

        messages.append({'role':'user', 'content':f"{delimiter} + {question} + {delimiter}"})

        # Send text to ChatGPT.
        print(f"Asking: {question}")
        response, usage = get_completion(messages)

        messages.append({"role": "assistant", "content":f"{response}"})

        print(usage)
        print(response + "\n")

        # Convert ChatGPT response into audio.
        text_to_speech(response)
        # Play audio of reponse.
        audio = AudioSegment.from_wav('result.wav')
        play(audio)

        count += 1
        if count > 4:
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

def speech_to_text(speech_file):
    client = speech.SpeechClient()

    with io.open(speech_file, "rb") as audio_file:
            content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US",
    )

    # Detects speech in the audio file
    response = client.recognize(config=config, audio=audio)

    stt = ""
    for result in response.results:
        stt += result.alternatives[0].transcript

    return stt

def text_to_speech(tts):
    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=tts)

    # Build the voice request, select the language code ("en-US") and the ssml
    voice1 = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    voice2 = texttospeech.VoiceSelectionParams(
        name = 'en-GB-Neural2-F',
        language_code = 'en-GB',
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice2, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open("result.wav", "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)

    return


def record_wav():
    form_1 = pyaudio.paInt16
    chans = 1
    samp_rate = 16000
    chunk = 4096
    max_silence_secs = 3
    threshold = 200
    dev_index = 1
    wav_output_filename = 'input.wav'

    audio = pyaudio.PyAudio()

    # Create pyaudio stream.
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index,input = True, \
                        frames_per_buffer=chunk)
    print("Listening for voice...")
    frames = []

    while True:
        data = stream.read(chunk)
        rms = audioop.rms(data, 2)  # Measure volume

        if rms > threshold:  # If volume exceeds threshold, voice detected
            frames.append(data)
            print("Recording...")
            silence = 0
        elif frames:
            # If there's already some recording and silence detected
            silence += chunk
            frames.append(data)

            # If silent for more than max_silence_secs, stop recording
            if silence / samp_rate >= max_silence_secs:
                break

    print("Finished recording")

    # Stop the stream, close it, and terminate the pyaudio instantiation.
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the audio frames as .wav file.
    with wave.open(wav_output_filename, 'wb') as wavefile:
        wavefile.setnchannels(chans)
        wavefile.setsampwidth(audio.get_sample_size(form_1))
        wavefile.setframerate(samp_rate)
        wavefile.writeframes(b''.join(frames))

    return

if __name__ == "__main__":
    main()

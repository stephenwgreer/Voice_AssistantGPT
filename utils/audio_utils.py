import io
import requests
import audioop
import pyaudio
import wave
import numpy as np
from playsound import playsound
import speech_recognition as sr

from google.cloud import speech

def speech_to_text():
    # Create a Recognizer instance
    recognizer = sr.Recognizer()

    # Use the Microphone as the audio source
    with sr.Microphone() as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")

        # Capture the audio
        audio_data = recognizer.listen(source)

        try:
            # Recognize speech using Google Web Speech API
            text = recognizer.recognize_google(audio_data)
            print("Transcription: ", text)
        except sr.UnknownValueError:
            print("Google Web Speech API could not understand the audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Web Speech API; {e}")
        
        return text
    
    # print("Transforming speech into text...")
    
    # client = speech.SpeechClient()

    # with io.open(speech_file, "rb") as audio_file:
    #         content = audio_file.read()

    # audio = speech.RecognitionAudio(content=content)

    # config = speech.RecognitionConfig(
    #     encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    #     language_code="en-US",
    # )

    # # Detects speech in the audio file
    # response = client.recognize(config=config, audio=audio)

    # stt = ""
    # for result in response.results:
    #     stt += result.alternatives[0].transcript

    # print("Transformation Complete")

    # return stt

def text_to_speech(tts, response_count, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_NAME):
    ELEVENLABS_VOICE_STABILITY = 0.30
    ELEVENLABS_VOICE_SIMILARITY = 0.75

    # Choose your favorite ElevenLabs voice
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    response = requests.get(url, headers=headers)

    ELEVENLABS_ALL_VOICES = response.json()["voices"]
    voices = ELEVENLABS_ALL_VOICES

    print("Transforming text into speech...")

    try:
        voice_id = next(filter(lambda v: v["name"] == ELEVENLABS_VOICE_NAME, voices))["voice_id"]
    except StopIteration:
        voice_id = voices[0]["voice_id"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": tts,
        "voice_settings": {
            "stability": ELEVENLABS_VOICE_STABILITY,
            "similarity_boost": ELEVENLABS_VOICE_SIMILARITY,
        }
    }
    response = requests.post(url, json=data, headers=headers)

    CHUNK_SIZE = 1024

    with open(f"response/result{response_count}.mp3", "wb") as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
    
    print("TTS Complete")

    return

# Helper function for the listener
def get_next_audio_frame(stream, CHUNK):
    """
    This function reads a chunk of audio data from the microphone and returns it.
    """
    data = stream.read(CHUNK)
    # Convert the byte data to numpy array
    audio_frame = np.frombuffer(data, dtype=np.int16)
    return audio_frame

def listener(handle):
    # Constants for audio stream
    FORMAT = pyaudio.paInt16 # Audio format (16-bit PCM)
    CHANNELS = 1 # Mono audio
    RATE = 16000 # Sample rate in Hz
    CHUNK = 512 # Number of frames per buffer
    DEV_INDEX = 1 # Device index found by p.get_device_info_by_index(ii)

    # create a PyAudio stream
    audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index = DEV_INDEX)
    
    print("Stream Opened")

    while True:
        keyword_index = handle.process(get_next_audio_frame(stream, CHUNK))
        if keyword_index >= 0:
            print("Keyword Detected")
            # Detection event logic/callback
            break
    
    return


def record_wav(stream, audio):
    form_1 = pyaudio.paInt16
    chans = 1
    samp_rate = 16000
    chunk = 512
    max_silence_secs = 2
    threshold = 200
    # dev_index = 1
    wav_output_filename = 'input.wav'
    
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

    print("Finished Recording")

    # Save the audio frames as .wav file.
    with wave.open(wav_output_filename, 'wb') as wavefile:
        wavefile.setnchannels(chans)
        wavefile.setsampwidth(audio.get_sample_size(form_1))
        wavefile.setframerate(samp_rate)
        wavefile.writeframes(b''.join(frames))

    return

def close_stream(stream, audio):
    # Stop the stream, close it, and terminate the pyaudio instantiation.
    stream.stop_stream()
    stream.close()
    audio.terminate()

    return

import os
from io import BytesIO
import pyaudio
import wave
from pynput import keyboard
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from openai import OpenAI
# Set the API keys (replace with your actual API keys)
ELEVENLABS_API_KEY = "sk_f8789524d1cfec38bce80749db8953a481c72012e01f9d35"
OPENAI_API_KEY = "sk-proj-F4qPXJoI9ynDfup8zJl4T3BlbkFJAVHDOglFIymmrXkEpbTy"
# Initialize ElevenLabs and OpenAI clients
ttsClient = ElevenLabs(api_key=ELEVENLABS_API_KEY)
aiClient = OpenAI(api_key=OPENAI_API_KEY)
# Initialize PyAudio
p = pyaudio.PyAudio()
# Function to list available audio input devices
def list_audio_devices():
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    devices = []
    for i in range(0, numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        devices.append(device_info)
        print(f"Device {i}: {device_info['name']}")
    return devices
# Select an appropriate audio input device
def select_audio_device():
    devices = list_audio_devices()
    # Select the first device (or any other logic to select the correct device)
    device_index = 0
    print(f"Selected Device {device_index}: {devices[device_index]['name']}")
    return device_index
# Function to record audio
def record_audio(device_index):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK)
    print("* recording")
    frames = []
    # Recording loop
    while recording:
        data = stream.read(CHUNK)
        frames.append(data)
    print("* done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
# Global variable to control recording state
recording = False
# Key press handler
def on_press(key):
    global recording
    if key == keyboard.Key.ctrl_r and not recording:  # Use alt_l for left Alt key
        recording = True
        print("Recording started...")
        record_audio(select_audio_device())
    elif key == keyboard.Key.esc:
        recording = False
        print("Recording stopped...")
        return False  # Stop listener
# Key release handler
def on_release(key):
    global recording
    if key == keyboard.Key.alt_l:
        recording = False
        print("Recording stopped...")
# Function to record audio
def record_audio(device_index):
    global recording  # Ensure recording is accessed correctly
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK)
    print("* recording")
    frames = []
    # Recording loop
    while recording:
        data = stream.read(CHUNK)
        frames.append(data)
    print("* done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
# Function to convert text to speech and play it
def text_to_speech_stream(text: str):
    response = ttsClient.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    audio_stream = BytesIO()
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)
    audio_stream.seek(0)
    return audio_stream
# Function to transcribe audio to text
def transcribe_audio(audio_file_path):
    with open(audio_file_path, 'rb') as audio_file:
        transcription = aiClient.audio.transcriptions.create("whisper-1", audio_file)
    return transcription['text']
# Conversation loop
def handle_conversation():
    text = "Hey, welcome to sports media's speechbot, I am svaz, how can I help you today"
    text_to_speech_stream(text)
    print("\nAI:", text)
    record = "AI: " + text + "\n"
    while True:
        # Wait for user to start recording
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
        transcript_result = transcribe_audio("input.wav")
        record += "User: " + transcript_result + "\n"
        print("\nYou: ", transcript_result)
        if transcript_result.lower() == "end":
            break
        response = aiClient.chat.completions.create(
            model='gpt-3.5-turbo-16k',
            messages=[
                {"role": "system", "content": 'You are a highly skilled AI. Answer the questions given within a maximum of 1000 characters. Here is a record of the conversation so far:\n\n' + record},
                {"role": "user", "content": transcript_result}
            ]
        )
        ai_response = response.choices[0].message['content']
        record += "AI: " + ai_response + "\n"
        print("\nAI: ", ai_response)
        text_to_speech_stream(ai_response)
# Start conversation
handle_conversation()
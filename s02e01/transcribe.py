import os
from dotenv import load_dotenv
import openai
import requests
from faster_whisper import WhisperModel

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

audio_folder = 'przesluchania'
model = WhisperModel('medium', device='cpu', compute_type='int8')

def transcribe_folder(audio_folder):

    for filename in os.listdir(audio_folder):
        if filename.lower().endswith('.m4a'):
            audio_path = os.path.join(audio_folder, filename)
            txt_filename = os.path.splitext(filename)[0] + '.txt'
            txt_path = os.path.join(audio_folder, txt_filename)

            print(f'Przetwarzanie: {filename}')

            segments, info = model.transcribe(audio_path, beam_size=5)

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f'Wykryto jezyk: {info.language}\n\n')
                for segment in segments:
                    f.write(f'[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}\n')

            print(f'Zapisano transkrypcje dla {txt_filename}')


transcribe_folder(audio_folder)

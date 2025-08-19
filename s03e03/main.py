import os
from dotenv import load_dotenv
import openai
import requests

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

openai.api_key = OPENAI_API_KEY

def read_file(directory, filename):
    with open(f'{directory}/{filename}', 'r', encoding='utf-8') as f:
        return f.read()

def read_prompt(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def send_to_centrala(task, answer):
    url = 'https://c3ntrala.ag3nts.org/report'
    data = {"task":task,
            "apikey":AIDEVS_API_KEY,
            "answer":answer
            }
    response = requests.post(url, json=data)
    
    return response.text



import os
from dotenv import load_dotenv
import openai
import requests

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

transcribed_files = 'przesluchania'

def list_txt_files(folder_path):
    return [f for f in os.listdir(folder_path) if f.endswith('.txt') and os.path.isfile(os.path.join(folder_path, f))]

def create_prompt(file_names):
    for file in file_names:
        with open(f'{transcribed_files}/{file}', 'r', encoding='utf-8') as f:
            with open('zeznania.txt', 'a', encoding='utf-8') as w_f:
                w_f.write(f'Zeznania osoby: {file.strip(".txt")}\n{f.read()}')

def send_prompt(zeznania, system_prompt):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role":"system", "content":system_prompt},
                {"role":"user","content":zeznania}
                ]
            )

    answer = response.choices[0].message.content
    return answer

def read_file(zeznania_file):
    with open(zeznania_file, 'r', encoding='utf-8') as f:
        return f.read()


file_names = list_txt_files(transcribed_files)
print(file_names)
#create_prompt(file_names)
zeznania = read_file('zeznania.txt')
system_prompt = read_file('prompt.txt')

print(send_prompt(zeznania, system_prompt))

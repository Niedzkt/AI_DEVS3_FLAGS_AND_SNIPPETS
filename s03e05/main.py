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

def send_query(query):
    url = 'https://c3ntrala.ag3nts.org/apidb'
    data = {
            "task":"database",
            "apikey":AIDEVS_API_KEY,
            "query":query
            }
    response = requests.post(url, json=data)

    return response

def ask_llm(users, connections, text):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role':'system',
                 'content':read_prompt('system_prompt.txt')},
                {'role':'user',
                 'content': f'Plik z uzytkownikami: {users} połączenia pomiędzy użytkownikami: {connections}. Na ich podstawie chcę uzyskać zapytanie do neo4j: {text}'
                 }
                ]
            )
    answer = response.choices[0].message.content
    return answer

def save_file(text, filename):
    with open(f'{filename}.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    
    return f'zapisano plik {filename}.txt'

while True:

    text = input('Polecenie dla modelu: ')
    
    answer = ask_llm(read_file('.','users.txt'),read_file('.','connections.txt'),text)

    print(f'Polecenie: {answer}')

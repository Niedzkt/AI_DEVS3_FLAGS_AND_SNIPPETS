import os
from dotenv import load_dotenv
import openai
import requests
import ast

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

openai.api_key = OPENAI_API_KEY

FACTS_DIR = 'pliki/facts'
RAPORTS_DIR = 'pliki'

def find_files(folder_path):
    txt_files = []

    for file_name in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file_name)
        if os.path.isfile(full_path):
            _, ext = os.path.splitext(file_name)
            ext_lower = ext.lower()
            if ext_lower == '.txt':
                txt_files.append(file_name)

    txt_files.sort()

    result = txt_files

    return result

def read_file(directory, filename):
    with open(f'{directory}/{filename}', 'r', encoding='utf-8') as f:
        return f.read()

def read_prompt(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def create_key_phrases(filename, text, facts=None):
    if facts and filename in facts:
        second_file = facts[filename]
        try:
            with open(f'{FACTS_DIR}/{second_file}','r', encoding='utf-8') as f:
                second_text = f.read()

            text += f'\n\n---\nDodatkowa zawartosc pliku {second_file}:\n{second_text}'
        except FileNotFoundError:
            print(f'Nie znaleziono pliku: {second_file}, pomijam...')

    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role':'system',
                 'content':read_prompt('system_prompt.txt')},
                {'role':'user',
                 'content':f'Nazwa pliku: {filename}. Tekst w nim zawarty: {text}'}
                ]
            )

    answer = response.choices[0].message.content

    return answer

def make_connections_facts_raports(facts_dict, raports_dict):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role':'system',
                 'content':read_prompt('raports_and_facts.txt')},
                {'role':'user',
                 'content': f'Pliki faktów: {facts_dict} Pliki raportów: {raports_dict}'
                 }
                ]
            )
    answer = response.choices[0].message.content
    return answer

def add_to_dict(dictionary, key, value):
    dictionary[key] = value
    return dictionary

def send_to_centrala(key_phrases_dict):
    url = 'https://c3ntrala.ag3nts.org/report'
    data = {"task":"dokumenty",
            "apikey":AIDEVS_API_KEY,
            "answer":key_phrases_dict
            }
    response = requests.post(url, json=data)
    
    return response.text

while True:
    raporty = find_files(RAPORTS_DIR)
    fakty = find_files(FACTS_DIR)
    raports_dict = {}
    facts_dict = {}
    connections = {}
    key_phrases_dict = {}

    option = input('1.Znajdź powiązania między faktami, a raportami')
    if option == '1':
        print(raporty)
        print(fakty)
        for raport in raporty:
            add_to_dict(raports_dict, raport, read_file(RAPORTS_DIR, raport))
            print('utworzono słownik raportów')

        for fakt in fakty:
            add_to_dict(facts_dict, fakt, read_file(FACTS_DIR, fakt))
            print('Utworzono słownik faktów')

        connections_str = make_connections_facts_raports(facts_dict, raports_dict)
        print(connections_str)
        connections = ast.literal_eval(connections_str)

        for raport in raporty:
            key_phrases = create_key_phrases(raport, read_file(RAPORTS_DIR, raport),connections)
            print(f'Nazwa pliku: {raport} a jego słowa kluczowe to: {key_phrases}')
            add_to_dict(key_phrases_dict, raport, key_phrases)

        print(send_to_centrala(key_phrases_dict))

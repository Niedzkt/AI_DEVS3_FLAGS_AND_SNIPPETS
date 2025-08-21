import os
from dotenv import load_dotenv
import openai
import requests
import ast
import re

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

openai.api_key = OPENAI_API_KEY

def string_to_dict(s: str) -> dict:
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        raise ValueError("Podany string nie jest poprawnym słownikiem w formacie Pythona.")

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

def ask_api(endpoint, query):
    url = f'https://c3ntrala.ag3nts.org/{endpoint}'
    data = {"apikey":AIDEVS_API_KEY, "query":query}
    response = requests.post(url, json=data)
    return response

def get_text():
    url = 'https://c3ntrala.ag3nts.org/dane/barbara.txt'
    response = requests.get(url)
    return response.text

def ask_llm(text):
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role':'system', 'content':read_prompt('system_prompt.txt')},
            {'role':'user', 'content': text}
        ]
    )
    answer = response.choices[0].message.content
    return answer

def clean_token(token):
    """Zwraca token tylko jeśli jest poprawną nazwą (wielkie litery i polskie znaki)."""
    if not token or token.startswith('[') or 'http' in token.lower():
        return None
    if re.fullmatch(r'[A-ZĄĆĘŁŃÓŚŹŻ\-]+', token):
        return token
    return None

while True:
    text_dict = ask_llm(get_text())
    try:
        info_dict = string_to_dict(text_dict)
        print('Otrzymany słownik jest poprawny: ', info_dict)
        break
    except ValueError:
        print('Niepoprawny string na słownik, ponownie przetwarzam...')

miasta_list = [clean_token(m) for m in info_dict['miasta'] if clean_token(m)]
imiona_list = [clean_token(i) for i in info_dict['imiona'] if clean_token(i)]

unikalne_miasta = miasta_list.copy()
unikalne_imiona = imiona_list.copy()

nowe_miasta = miasta_list.copy()
nowe_imiona = imiona_list.copy()

miasta_barbary = []  
while nowe_miasta or nowe_imiona:
    aktualne_nowe_imiona = []
    for miasto in nowe_miasta:
        response_text = ask_api('places', miasto).text
        try:
            response_dict = string_to_dict(response_text)
        except ValueError:
            continue

        for nowe_imie in response_dict.get('message', '').split():
            czysty_imie = clean_token(nowe_imie)
            if czysty_imie and czysty_imie not in unikalne_imiona:
                unikalne_imiona.append(czysty_imie)
                aktualne_nowe_imiona.append(czysty_imie)
    
    aktualne_nowe_miasta = []
    for imie in nowe_imiona:
        response_text = ask_api('people', imie).text
        try:
            response_dict = string_to_dict(response_text)
        except ValueError:
            continue

        for nowe_miasto in response_dict.get('message', '').split():
            czysty_miasto = clean_token(nowe_miasto)
            if czysty_miasto and czysty_miasto not in unikalne_miasta:
                unikalne_miasta.append(czysty_miasto)
                aktualne_nowe_miasta.append(czysty_miasto)

            if imie == "BARBARA" and czysty_miasto and czysty_miasto not in miasta_barbary:
                miasta_barbary.append(czysty_miasto)
    
    nowe_miasta = aktualne_nowe_miasta
    nowe_imiona = aktualne_nowe_imiona

print("Finalna lista unikalnych miast:", sorted(unikalne_miasta))
print("Finalna lista unikalnych imion:", sorted(unikalne_imiona))
print("Miasta, w których pojawiła się Barbara:", sorted(miasta_barbary))

for miasto in unikalne_miasta:
    print(send_to_centrala('loop', miasto))

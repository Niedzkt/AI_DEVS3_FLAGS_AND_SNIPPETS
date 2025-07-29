import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

LOGIN = 'tester'
PASSWORD = '574e112a'

def send_request(url):
    response = requests.get(url)

    if response.status_code == 200:

        soup = BeautifulSoup(response.text, 'html.parser')

        p = soup.find('p', id='human-question')

        if p:
            question = p.get_text(strip=True).replace('Question:', '', 1).strip()
            print(question)
            return question
        else:
            print(f'Nie znaleziono elementu z pytaniem')
            return 0
    else:
        print(f'Blad: {response.status_code}')
        return 0

def clear_request(url):
    response = requests.get(url)

    if response.status_code == 200:
        html = response.text
        print(html)
        
    else:
        print(f'Blad: {response.status_code}')
        return 0


def send_question_to_llm(question):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content": "Masz za zadanie odpowiedziec na pytanie tylko i wylacznie liczba. Nigdy nie odpowiadaj pelnymi zdaniami"},
            {"role":"user", "content": question}
            ]
        )
    
    answer = response.choices[0].message.content

    return answer

def send_post(url, answer):

    headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }

    data = {
            'username': LOGIN,
            'password': PASSWORD,
            'answer': answer
            }

    response = requests.post(url, headers=headers, data=data)
    print(f'Status code odpowiedzi przy POST: {response.status_code}')
    print('Odpowiedz serwera:')
    print(response.text)


url = 'https://xyz.ag3nts.org/'

question = send_request(url)
answer = send_question_to_llm(question)
send_post(url, answer)
clear_request(url+'files/0_13_4b.txt')

import os
from dotenv import load_dotenv
import openai
import requests


load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

def load_prompt():
    with open('prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
    print(prompt)

    return prompt

def download_agent_data(url):
    response = requests.get(url)

    return response.text


def censorship(agent_datai, prompt):
    
    response = openai.chat.completions.create(
            model = "gpt-4o-mini",
            messages=[
                {"role":"system", "content": prompt},
                {"role":"user", "content": agent_data}
                ]
            )

    answer = response.choices[0].message.content
    print(f'Zacenzurowane dane:\n{answer}')

    return answer

def send_data_to_endpoint(api_key, answer):
    url = "https://c3ntrala.ag3nts.org/report"

    payload = {
            "task":"CENZURA",
            "apikey":api_key,
            "answer":answer
            }

    response = requests.post(url, json=payload)
    print("Status: ", response.status_code)
    print("Odpowiedź:\n", response.text)


url = input("Podaj url dla danych: ")
api_key = input("Podaj swój API key: ")
agent_data = download_agent_data(url)
prompt = load_prompt()

answer = censorship(agent_data, prompt)
send_data_to_endpoint(api_key, answer)
print("Zakonczone")

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

def ask_llm(table_list, tables_dict, text):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {'role':'system',
                 'content':read_prompt('system_prompt.txt')},
                {'role':'user',
                 'content': f'Lista tabel: {table_list} oraz ich schematy: {tables_dict}. Na ich podstawie chcę uzyskać zapytanie sql które {text}'
                 }
                ]
            )
    answer = response.choices[0].message.content
    return answer

while True:
    tables_dict = {}
    response = send_query('show tables')
    data = response.json()
    table_list = [list(item.values())[0] for item in data['reply']]
    print(table_list)
    for value in table_list:
        response = send_query(f'show create table {value}')
        data = response.json()

        row = data['reply'][0]
        table_name = row['Table']
        create_stmt = row['Create Table']
        tables_dict[table_name] = create_stmt

    text = input('Podaj zapytanie do systemu: ')
    query = ask_llm(table_list, tables_dict, text)
    answer = send_query(query)
    print(f'Zapytanie do bazy: {query}\n\nOdpowiedź bazy: {answer.text}')
    data = answer.json()
    dc_table_list = [list(item.values())[0] for item in data['reply']]
    print(f'Lista datacenter id: {dc_table_list}')
    print(send_to_centrala('database',dc_table_list))

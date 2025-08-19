import os
from dotenv import load_dotenv
import openai
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import glob
import uuid
from datetime import datetime

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

openai.api_key = OPENAI_API_KEY

client = QdrantClient(url='http://localhost:6333')

client.recreate_collection(
        collection_name='raporty',
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )

FILES_DIR = 'pliki/do-not-share'

def save_files_to_db(folder_path):
    for file_path in glob.glob(f'{folder_path}/*.txt'):
        file_name = file_path.split('/')[-1]
        print(f'Przetwarzanie: {file_name}')
        date_str = file_name.replace('.txt','').replace('_','-')
        date_obj = datetime.strptime(date_str,'%Y-%m-%d')

        with open(file_path,'r',encoding='utf-8') as f:
            content = f.read()

        embedding = get_embedding(content)

        client.upsert(
                collection_name = 'raporty',
                points=[{
                    'id':str(uuid.uuid4()),
                    'vector':embedding,
                    'payload':{
                        'date':date_obj.strftime('%Y-%m-%d'),
                        'filename':file_name,
                        'text':content
                        }
                    }]
                )

def read_file(directory, filename):
    with open(f'{directory}/{filename}', 'r', encoding='utf-8') as f:
        return f.read()

def read_prompt(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def get_embedding(text):
    response = openai.embeddings.create(
            model='text-embedding-3-large',
            input=text
            )
    return response.data[0].embedding

def send_to_centrala(task, answer):
    url = 'https://c3ntrala.ag3nts.org/report'
    data = {"task":task,
            "apikey":AIDEVS_API_KEY,
            "answer":answer
            }
    response = requests.post(url, json=data)
    
    return response.text

print('Przetwarzanie plikow do bazy...')
save_files_to_db(FILES_DIR)
print('Pliki przetworzone.')

query = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
query_embedding = get_embedding(query)

search_result = client.search(
        collection_name='raporty',
        query_vector=query_embedding,
        limit=1
        )

for hit in search_result:
    print("Score:", hit.score)
    print("Data raportu: ", hit.payload['date'])
    answer = hit.payload['date']
    print('Plik: ',hit.payload['filename'])
    print('Fragment: ',hit.payload['text'][:200], '...')

print(send_to_centrala('wektory',answer))

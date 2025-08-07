import os
from dotenv import load_dotenv
import openai
import requests
import json

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

openai.api_key = OPENAI_API_KEY

url = f'https://c3ntrala.ag3nts.org/data/{AIDEVS_API_KEY}/robotid.json'

def get_info_about_robot(url):
    response = requests.get(url)
    data = response.json()    

    return data

def load_prompt():
    with open('prompt.txt', 'r', encoding='utf-8') as f:
        text = f.read()
        return text

def send_description(robot_desc, system_prompt):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role":"system", "content":system_prompt},
                {"role":"user", "content":json.dumps(robot_desc, ensure_ascii=False)}
                ]
            )

    answer = response.choices[0].message.content
    return answer

def create_image(prompt):
    response = openai.images.generate(
            model='dall-e-3',
            prompt=prompt,
            size='1024x1024',
            quality='standard',
            n=1,
            )
    image_url=response.data[0].url
    print(image_url)
    return image_url

def send_image_to_centrala(image_url,api_key):
    url = "https://c3ntrala.ag3nts.org/report"
    payload = {"task":"robotid",
               "apikey":api_key,
               "answer":image_url
               }
    response = requests.post(url, json=payload)
    print("status code: ", response.status_code)
    print('Odpowiedz: ', response.text)



system_prompt = load_prompt()
user_prompt = get_info_about_robot(url)
robot_desc = send_description(user_prompt,system_prompt)
img_url = create_image(robot_desc)
send_image_to_centrala(img_url,AIDEVS_API_KEY)

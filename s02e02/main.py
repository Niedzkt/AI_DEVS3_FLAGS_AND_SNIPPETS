import os
from dotenv import load_dotenv
import openai
import requests
import base64

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

IMAGE_FOLDER = "images/"

def image_encode(image):
    with open(f'{IMAGE_FOLDER}{image}','rb') as f:
        bin_data = f.read()
        enc_base64 = base64.b64encode(bin_data)

    base64_string = enc_base64.decode('utf-8')

    return base64_string

def send_image(imageBase64):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role":"system",
                 "content":"Jesteś systemem wykrywającym lokalizacje miasta na bazie przekazanego fragmentu mapy. Twoim zadaniem jest wskazać miasto z których dany fragment mapy wystepuje"},
                {"role":"user",
                 "content": [
                     {
                         "type":"image_url",
                         "image_url": {
                             "url": f"data:image/jpeg;base64,${imageBase64}",
                             "detail": "high"
                             }
                         },
                     {
                         "type": "text",
                         "text": "Wskaż z jakiego miasta występuje fragment mapy"
                         }
                     ]
                 }
                ]
            
    )

    answer = response.choices[0].message.content
    return answer






for i in range(4):
    image = f'image_{i+1}.png'
    img_base64 = image_encode(image)
    print(send_image(img_base64))
    

    i = i+1

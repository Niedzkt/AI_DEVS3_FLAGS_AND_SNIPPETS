import os
from dotenv import load_dotenv
import openai
import requests
from faster_whisper import WhisperModel
from PIL import Image
import pytesseract

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

openai.api_key = OPENAI_API_KEY
model = WhisperModel('medium', device='cpu', compute_type='int8')

def find_files():
    folder_path = 'pliki'
    txt_files = []
    mp3_files = []
    png_files = []

    for file_name in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file_name)
        if os.path.isfile(full_path):
            _, ext = os.path.splitext(file_name)
            ext_lower = ext.lower()
            if ext_lower == '.txt':
                txt_files.append(file_name)
            elif ext_lower == '.mp3':
                mp3_files.append(file_name)
            elif ext_lower == '.png':
                png_files.append(file_name)

    txt_files.sort()
    mp3_files.sort()
    png_files.sort()

    result = [txt_files, mp3_files, png_files]

    return result

def read_txt_file(file_name):
    with open(f'pliki/{file_name}', 'r', encoding='utf-8') as f:
        return f.read()

def read_mp3_file(file_name):
    segments, info = model.transcribe(f'pliki/{file_name}', beam_size=5)
    
    result = ""

    for segment in segments:
        result += f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}\n"
    
    return result

def read_png_file(file_name):
    image = Image.open(f'pliki/{file_name}')
    text = pytesseract.image_to_string(image, lang='pol')
    return text

def read_prompt(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return f.read()

def categorize_text(text_to_send):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role":"system",
                 "content":read_prompt('system_prompt.txt')},
                {"role":"user",
                 "content":text_to_send}
                ]
            )
    answer = response.choices[0].message.content

    return answer

def send_to_centrala(people_list, hardware_list):
    url = 'https://c3ntrala.ag3nts.org/report'
    data = {"task":"kategorie",
            "apikey":AIDEVS_API_KEY,
            "answer":{
                "people":people_list,
                "hardware":hardware_list
                }
            }
    response = requests.post(url, json=data)
    
    return response








while True:
    print('Wczytywanie plików...')
    files = find_files()
    print('Wczytano dowody.')
    people_list = []
    hardware_list =[]

    option = input('Wybierz co chcesz zrobic: \n1.Przetworz pliki tekstowe\n2.Przetworz pliki mp3\n3.Przetworz pliki png\n4.Wszystko naraz\n0.Zamknij program\n')


    if option == '1':
        for file in files[0]:
            print('\n-----------------------------------------------------')
            #print(f'{read_txt_file(file)}\n')
            text = read_txt_file(file)
            result = categorize_text(text)
            if result == '1':
                print(f'Plik o nazwie {file} otrzymal kategorie 1 - Ludzie')
                people_list.append(file)
            elif result == '2':
                print(f'Plik o nazwie {file} otrzymal kategorie 2 - Hardware')
                hardware_list.append(file)
            elif result == '0':
                print(f'Plik o nazwie {file} nie pasuje do żadnej z kategorii')
            

    elif option == '2':
        for file in files[1]:
            print('\n-----------------------------------------------------')
            #print(f'{read_mp3_file(file)}\n')
            text = read_mp3_file(file)
            print(text) 
            result = categorize_text(text)
            if result == '1':
                print(f'Plik o nazwie {file} otrzymal kategorie 1 - Ludzie')
                people_list.append(file)
            elif result == '2':
                print(f'Plik o nazwie {file} otrzymal kategorie 2 - Hardware')
                hardware_list.append(file)
            elif result == '0':
                print(f'Plik o nazwie {file} nie pasuje do żadnej z kategorii')
    

    elif option == '3':
        for file in files[2]:
            print('\n-----------------------------------------------------')
            #print(f'{read_png_file(file)}\n')
            text = read_png_file(file)
            result = categorize_text(text)
            if result == '1':
                print(f'Plik o nazwie {file} otrzymal kategorie 1 - Ludzie')
                people_list.append(file)
            elif result == '2':
                print(f'Plik o nazwie {file} otrzymal kategorie 2 - Hardware')
                hardware_list.append(file)
            elif result == '0':
                print(f'Plik o nazwie {file} nie pasuje do żadnej z kategorii')

    elif option == '4':
        for file in files[0]:
            print('\n-----------------------------------------------------')
            #print(f'{read_txt_file(file)}\n')
            text = read_txt_file(file)
            result = categorize_text(text)
            if result == '1':
                print(f'Plik o nazwie {file} otrzymal kategorie 1 - Ludzie')
                people_list.append(file)
            elif result == '2':
                print(f'Plik o nazwie {file} otrzymal kategorie 2 - Hardware')
                hardware_list.append(file)
            elif result == '0':
                print(f'Plik o nazwie {file} nie pasuje do żadnej z kategorii')
            

        for file in files[1]:
            print('\n-----------------------------------------------------')
            #print(f'{read_txt_file(file)}\n')
            text = read_mp3_file(file)
            result = categorize_text(text)
            if result == '1':
                print(f'Plik o nazwie {file} otrzymal kategorie 1 - Ludzie')
                people_list.append(file)
            elif result == '2':
                print(f'Plik o nazwie {file} otrzymal kategorie 2 - Hardware')
                hardware_list.append(file)
            elif result == '0':
                print(f'Plik o nazwie {file} nie pasuje do żadnej z kategorii')
            
        for file in files[2]:
            print('\n-----------------------------------------------------')
            #print(f'{read_png_file(file)}\n')
            text = read_png_file(file)
            result = categorize_text(text)
            if result == '1':
                print(f'Plik o nazwie {file} otrzymal kategorie 1 - Ludzie')
                people_list.append(file)
            elif result == '2':
                print(f'Plik o nazwie {file} otrzymal kategorie 2 - Hardware')
                hardware_list.append(file)
            elif result == '0':
                print(f'Plik o nazwie {file} nie pasuje do żadnej z kategorii')


        print(f'Kategoria ludzie ma pliki: {people_list}\nKategoria Hardware ma pliki: {hardware_list}')
        
        print('Wysylanie pliku do centrali...')
        centrala_response = send_to_centrala(people_list,hardware_list)
        print(centrala_response.status_code)
        print(centrala_response.text)

    elif option == '0':
        break

import os
from dotenv import load_dotenv
import openai
import requests
from faster_whisper import WhisperModel
from bs4 import BeautifulSoup,NavigableString
from urllib.parse import urljoin
import base64

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AIDEVS_API_KEY = os.getenv('AIDEVS_API_KEY')

BASE_URL = 'https://c3ntrala.ag3nts.org/dane/arxiv-draft.html'
OUTPUT_DIR = 'pobrane'
IMAGES_DIR = os.path.join(OUTPUT_DIR, 'obrazy')
AUDIO_DIR = os.path.join(OUTPUT_DIR, 'audio')

openai.api_key = OPENAI_API_KEY
model = WhisperModel('medium', device='cpu', compute_type='int8')

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

headers = {'User-Agent':'Mozilla/5.0'}
response = requests.get(BASE_URL, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, 'html.parser')

def find_files(folder_path):
    mp3_files = []
    png_files = []

    for file_name in os.listdir(folder_path):
        full_path = os.path.join(folder_path, file_name)
        if os.path.isfile(full_path):
            _, ext = os.path.splitext(file_name)
            ext_lower = ext.lower()
            if ext_lower == '.mp3':
                mp3_files.append(file_name)
            elif ext_lower == '.png':
                png_files.append(file_name)

    mp3_files.sort()
    png_files.sort()

    result = [mp3_files, png_files]

    return result

def download_file(url, folder):
    filename = url.split('/')[-1].split('?')[0]
    filepath = os.path.join(folder, filename)

    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f'Pobrano: {filename}')
    except Exception as e:
        print(f'Błąd pobierania {url}: {e}')

def download_all_files():
    with open(os.path.join(OUTPUT_DIR, "mainpage.html"), "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Zapisano stronę główną jako mainpage.html")

    for img_tag in soup.find_all('img'):
        img_url = img_tag.get('src')

        if img_url:
            full_url = urljoin(BASE_URL, img_url)
            download_file(full_url, IMAGES_DIR)

    for audio_tag in soup.find_all('a', href=True):
        href = audio_tag['href']
        if href.lower().endswith('mp3'):
            full_url = urljoin(BASE_URL, href)
            download_file(full_url, AUDIO_DIR)

    print('Pobrano wszystko')

def html_to_markdown(html_path, img_descriptions=None, mp3_descriptions=None):
    img_descriptions = img_descriptions or []
    mp3_descriptions = mp3_descriptions or []

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    markdown_parts = []
    img_index = 0
    mp3_index = 0

    for element in soup.descendants:
        if element.name == "img":
            desc = img_descriptions[img_index] if img_index < len(img_descriptions) else "Obraz"
            markdown_parts.append(f"![{desc}](obraz_{img_index+1}.jpg)")
            img_index += 1
        elif element.name == "a" and element.get("href", "").lower().endswith(".mp3"):
            desc = mp3_descriptions[mp3_index] if mp3_index < len(mp3_descriptions) else "Audio"
            markdown_parts.append(f"[{desc}](audio_{mp3_index+1}.mp3)")
            mp3_index += 1
        elif isinstance(element, NavigableString):
            text = element.strip()
            if text:
                markdown_parts.append(text)

    return "\n\n".join(markdown_parts)


def image_encode(image):
    with open(f'pobrane/obrazy/{image}','rb') as f:
        bin_data = f.read()
        enc_base64 = base64.b64encode(bin_data)

    base64_string = enc_base64.decode('utf-8')

    return base64_string

def send_image(imageBase64):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role":"system",
                 "content":"Jesteś systemem opisującym zdjęcia. Twoim zadaniem jest dokładne opisanie zdjęcia które zostaje ci przekazane. Opis ma być jak najbardziej dokładny i zgodny z tym co znajduje się na przekazanym zdjęciu."},
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
                         "text": "Opisz dokładnie co znajduje się na zdjęciu"
                         }
                     ]
                 }
                ]       
    )
    answer = response.choices[0].message.content
    return answer

def read_mp3_file(file_name):
    segments, info = model.transcribe(f'pobrane/audio/{file_name}', beam_size=5)

    result = ""

    for segment in segments:
        result += f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}\n"

    return result

def save_to_file(description, filename):
    with open(f'opisy/{filename}.txt', 'w', encoding='utf-8') as f:
        f.write(description)
        print(f'Opis: \n{description}\n\n zapisano do pliku {filename}')

def load_file(filename):
    with open(f'opisy/{filename}', 'r', encoding='utf-8') as f:
        print(f'Wczytano opis dla pliku: {filename}')
        return f.read()

def download_questions():
    url = f'https://c3ntrala.ag3nts.org/data/{AIDEVS_API_KEY}/arxiv.txt'
    response = requests.get(url)

    return response.text

def create_dict(text):
    questions = dict(
            line.split('=',1)
            for line in text.splitlines()
            if line.strip()
            )
    return questions

def load_context(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def ask_llm_for_answers(questions,context):
    response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role":"system",
                 "content":f'Jestes systemem który ma za zadanie odpowiadać na pytania na bazie przekazanych informacji. Odpowiadasz krótko i jednym zdaniem. Dane z których masz brać odpowiedzi: {context}'},
                {"role":"user",
                 "content":questions}
                ]
            )
    answer = response.choices[0].message.content

    return answer

def send_to_centrala(answers):
    url = 'https://c3ntrala.ag3nts.org/report'
    data = {"task":"arxiv",
            "apikey":AIDEVS_API_KEY,
            "answer":answers
            }
    response = requests.post(url,json=data)
    return response

########################################################################################################

while True:
    option = input('Wybierz opcje: \n1.Pobierz strone i pliki\n2.Stworz opisy\n3.Stworz markdown\n4.Zacznij odpowiadac na pytania do centrali i wyslij wyniki\n')
    if option == '1':
        download_all_files()
    elif option == '2':
        obrazy = find_files('pobrane/obrazy')
        audio = find_files('pobrane/audio')
        for file in obrazy[1]:
            save_to_file(send_image(image_encode(file)),file)
        for file in audio[0]:
            save_to_file(read_mp3_file(file),file)
    elif option == '3':
        md_text = html_to_markdown('pobrane/mainpage.html',
                                   img_descriptions=[load_file('rynek.png.txt'),load_file('rynek_glitch.png.txt'),load_file('fruit01.png.txt'),load_file('fruit02.png.txt'),load_file('strangefruit.png.txt'),load_file('resztki.png.txt')],
                                   mp3_descriptions=[load_file('rafal_dyktafon.mp3.txt')]
                                   )
        with open('mainpage.md','w',encoding='utf-8') as f:
            f.write(md_text)

        print('Plik md z html zostal utworzony')
    elif option == '4':
        questions = create_dict(download_questions())
        context = load_context('mainpage.md')
        answers = {}
        for key, value in questions.items():
            print(f'Pytanie" {value}')
            answer = ask_llm_for_answers(value, context)
            print(f'Odpowiedz: {answer}')
            answers[key] = answer
        
        print(f'Odpowiedz z centrali: {send_to_centrala(answers).text}')






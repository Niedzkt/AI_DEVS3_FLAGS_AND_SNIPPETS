import os
from dotenv import load_dotenv
import openai
import requests
import json
import base64

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

def ask_centrala(task, answer):
    url = 'https://c3ntrala.ag3nts.org/report'
    data = {"task": task, "apikey": AIDEVS_API_KEY, "answer": answer}
    print(f"\n>>> [CENTRALA REQUEST] {data}")
    response = requests.post(url, json=data)
    print(f"<<< [CENTRALA RESPONSE] {response.text}\n")
    return response.text

def get_website(img):
    url = 'https://centrala.ag3nts.org/dane/barbara/'
    print(f"[DOWNLOAD] próbuję pobrać {url}{img}")
    response = requests.get(f'{url}{img}')
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise ValueError(f"URL nie zawiera obrazu. Typ: {content_type}")

    img_base64 = base64.b64encode(response.content).decode("utf-8")
    print(f"[OK] pobrano {img}, długość base64={len(img_base64)}")
    return img_base64

def send_image(imageBase64, system_prompt, instruction):
    print("[VISION] wysyłam obraz do modelu vision...")
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",
             "content": [
                 {
                     "type": "image_url",
                     "image_url": {
                         "url": f"data:image/jpeg;base64,{imageBase64}",
                         "detail": "high"
                     }
                 },
                 {"type": "text", "text": instruction}
             ]
             }
        ]
    )
    answer = response.choices[0].message.content
    print(f"[VISION OUTPUT] {answer}\n")
    return answer

def ask_llm(system_prompt, text):
    print("[BRAIN] wysyłam tekst do modelu brain...")
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': text}
        ]
    )
    answer = response.choices[0].message.content
    print(f"[BRAIN OUTPUT] {answer}\n")
    return answer

# ====== START WORKFLOW ======
brain_prompt = read_prompt('brain_prompt.txt')
images_prompt = read_prompt('images_prompt.txt')

print("=== [START] ===")
first_message = ask_centrala('photos', 'START')

first_answer = ask_llm(brain_prompt, first_message)
data = json.loads(first_answer)

img_list = data['img_name']
if isinstance(img_list, str):
    img_list = [img_list]

print(f"[INFO] Lista plików od centrali: {img_list}")

final_good_images = []

for img in img_list:
    current_img = img.strip("[]' ")  
    print(f"\n--- Rozpoczynam przetwarzanie obrazu: {current_img} ---")

    while True:
        try:
            img_base64 = get_website(current_img)
        except Exception as e:
            print(f"[ERROR] Nie udało się pobrać {current_img}: {e}")
            break

        vision_analysis = send_image(img_base64, images_prompt, "Opisz przekazane zdjęcie")

        brain_decision = ask_llm(brain_prompt, vision_analysis)
        decision_data = json.loads(brain_decision)

        action = decision_data["action"]
        print(f"[DECISION] action={action}, file={decision_data['img_name']}")

        if action == "FINISH":
            print(f"[SUCCESS] Zdjęcie {current_img} uznane za poprawne ✅")
            final_good_images.append(current_img)
            break
        else:
            cmd = f"{action} {current_img}"
            centrala_resp = ask_centrala("photos", cmd)

            centrala_analysis = ask_llm(brain_prompt, centrala_resp)
            centrala_data = json.loads(centrala_analysis)

            
            if "img_name" in centrala_data:
                new_img = centrala_data["img_name"]
                print(f"[INFO] Nowa nazwa pliku z centrali: {new_img}")

                if isinstance(new_img, list):
                    if len(new_img) > 0:
                        current_img = new_img[0]
                    else:
                        print("[ERROR] img_name to pusta lista ❌")
                        break
                else:
                    current_img = new_img
            else:
                print(f"[ERROR] Brak img_name w odpowiedzi centrali. Przerywam ❌")
                break
print("\n=== [FAZA KOŃCOWA: Rysopis Barbary] ===")
descriptions = []
for good_img in final_good_images:
    img_base64 = get_website(good_img)
    desc = send_image(img_base64, images_prompt, "Przygotuj szczegółowy opis Barbary")
    descriptions.append(desc)

final_report = ask_llm(brain_prompt, json.dumps(descriptions))
print("\n>>> Wstępny rysopis Barbary <<<\n")
print(final_report)

while True:
    centrala_resp = ask_centrala("photos", final_report)

    centrala_feedback = ask_llm(brain_prompt, centrala_resp)
    print(f"[BRAIN on FINAL REPORT] {centrala_feedback}")

    try:
        feedback_data = json.loads(centrala_feedback)
    except Exception:
        print("[ERROR] Nie udało się sparsować odpowiedzi mózgu dla centrali.")
        break

    action = feedback_data.get("action")
    if action == "FINISH":
        print("\n✅ Centrala zaakceptowała rysopis Barbary!\n")
        break
    else:
        print(f"[INFO] Centrala sugeruje poprawki, ponawiam wysyłkę...")
        final_report = feedback_data.get("corrected_report", final_report)

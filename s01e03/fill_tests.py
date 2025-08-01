import json
from pathlib import Path
from typing import Any, Tuple
import openai
import time
import os
from dotenv import load_dotenv
import openai
import requests


load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY



def path_to_str(path: Tuple):
    out = "root"
    for p in path:
        if isinstance(p, int):
            out += f"[{p}]"
        else:
            out += f'["{p}"]'
    return out

def collect_test_blocks(obj: Any, path: Tuple = ()):
    found = []
    if isinstance(obj, dict):
        if 'test' in obj and isinstance(obj['test'], dict):
            # tylko jeśli istnieje 'q'
            if 'q' in obj['test']:
                found.append((obj['test'], path + ('test',)))
        for k, v in obj.items():
            found.extend(collect_test_blocks(v, path + (k,)))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(collect_test_blocks(item, path + (idx,)))
    return found

def connect_to_llm(question: str) -> str:
    system_prompt = (
        "You are a helpful assistant. Answer all questions in English. "
        "If you don't know the answer, say 'I don't know.' Be concise and factual."
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.2,
            max_tokens=300,
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print(f"LLM call failed for question '{question}': {e}. Retrying once...")
        time.sleep(1)
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.2,
                max_tokens=300,
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e2:
            print(f"Second attempt failed: {e2}. Returning placeholder.")
            return "ERROR: could not fetch answer"

def fill_tests_with_llm(json_path: Path, output_path: Path):
    data = json.loads(json_path.read_text(encoding='utf-8'))
    test_blocks = collect_test_blocks(data)
    if not test_blocks:
        print("Nie znaleziono żadnych bloków z 'test'.")
        return

    for test_obj, path in test_blocks:
        q = test_obj.get('q', '').strip()
        if not q:
            print(f"{path_to_str(path)}: brak pytania 'q', pomijam.")
            continue
        print(f"Processing {path_to_str(path)} question: {q}")
        answer = connect_to_llm(q)
        print(f" -> answer: {answer}")
        test_obj['a'] = answer

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\nZapisano zaktualizowany JSON z odpowiedziami w '{output_path}'.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Wypełnij pola test.q przez LLM i wpisz odpowiedź do test.a")
    parser.add_argument("input", help="ścieżka do pliku JSON")
    parser.add_argument("output", help="ścieżka docelowa zapisu")
    args = parser.parse_args()

    fill_tests_with_llm(Path(args.input), Path(args.output))

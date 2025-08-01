import json
import argparse
from pathlib import Path
import os
import sys

try:
    import requests
except ImportError:
    requests = None

def build_wrapper(inner_json: dict, task: str, external_apikey: str) -> dict:
    return {
        "task": task,
        "apikey": external_apikey,
        "answer": inner_json
    }

def main():
    parser = argparse.ArgumentParser(description="Zbuduj wrapper JSON i opcjonalnie wyślij go na API.")
    parser.add_argument("input", help="ścieżka do wejściowego pliku JSON (np. poprawione.json)")
    parser.add_argument("output", help="ścieżka do zapisu wrappera (np. payload.json)")
    parser.add_argument("--task", default="JSON", help="pole task w wrapperze (domyślnie 'JSON')")
    parser.add_argument("--apikey", help="API key do wstawienia w wrapper. Jeśli pominięte, bierze z env EXTERNAL_API_KEY")
    parser.add_argument("--send-to", help="opcjonalny URL do którego zrobione będzie POST z wrapperem")
    parser.add_argument("--header", action="append", help="dodatkowy nagłówek HTTP w formacie 'Klucz: Wartość' przy wysyłce")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Błąd: nie znaleziono pliku wejściowego {in_path}", file=sys.stderr)
        sys.exit(1)

    try:
        inner = json.loads(in_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Nie udało się sparsować wejściowego JSON-a: {e}", file=sys.stderr)
        sys.exit(1)

    apikey = args.apikey or os.environ.get("EXTERNAL_API_KEY")
    if not apikey:
        print("Nie podano apikey ani nie ma zmiennej środowiskowej EXTERNAL_API_KEY.", file=sys.stderr)
        sys.exit(1)

    wrapper = build_wrapper(inner, args.task, apikey)

    out_path = Path(args.output)
    out_path.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Zapisano wrapper do {out_path}")

    if args.send_to:
        if requests is None:
            print("Biblioteka requests nie jest zainstalowana; nie można wysłać. Zainstaluj ją: pip install requests", file=sys.stderr)
            return
        headers = {"Content-Type": "application/json"}
        if args.header:
            for h in args.header:
                if ":" in h:
                    k, v = h.split(":", 1)
                    headers[k.strip()] = v.strip()
        try:
            print(f"Wysyłam POST do {args.send_to} ...")
            resp = requests.post(args.send_to, json=wrapper, headers=headers, timeout=30)
            print(f"Status: {resp.status_code}")
            try:
                print("Odpowiedź serwera:")
                print(resp.text)
            except:
                pass
        except Exception as e:
            print(f"Błąd przy wysyłce: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()

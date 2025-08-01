import json
from pathlib import Path
from typing import Any, Tuple, Union

def path_to_str(path: Tuple[Union[str, int], ...]) -> str:
    out = "root"
    for p in path:
        if isinstance(p, int):
            out += f"[{p}]"
        else:
            out += f'["{p}"]'
    return out

def collect_and_print_questions(obj: Any, path: Tuple = (), in_test_branch: bool = False):
    
    current_in_test = in_test_branch or any(isinstance(p, str) and p.lower() == "test" for p in path)

    if isinstance(obj, dict):
        if current_in_test:
            if 'question' in obj and isinstance(obj['question'], str):
                print(f"{path_to_str(path + ('question',))}: {obj['question']}")
            if 'q' in obj and isinstance(obj['q'], str):
                print(f"{path_to_str(path + ('q',))}: {obj['q']}")
        for k, v in obj.items():
            collect_and_print_questions(v, path + (k,), current_in_test)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            collect_and_print_questions(item, path + (idx,), current_in_test)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Wypisz pytania tylko z gałęzi 'test' (nie 'test-data').")
    parser.add_argument("input", help="ścieżka do poprawnego pliku JSON")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding='utf-8'))
    collect_and_print_questions(data)

if __name__ == "__main__":
    main()

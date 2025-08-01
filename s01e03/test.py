import json
import re
from pathlib import Path
from typing import Any, Tuple, Union, List

ARITH_EXPR = re.compile(r'^\s*(-?\d+(?:\.\d+)?)\s*([\+\-\*/])\s*(-?\d+(?:\.\d+)?)\s*$')
TRAILING_COMMA_BEFORE_CLOSER = re.compile(r',\s*(?P<closer>[\}\]])')  

def eval_simple(expr: str) -> Union[float, None]:
    m = ARITH_EXPR.match(expr)
    if not m:
        return None
    a, op, b = m.group(1), m.group(2), m.group(3)
    a, b = float(a), float(b)
    try:
        if op == '+':
            return a + b
        if op == '-':
            return a - b
        if op == '*':
            return a * b
        if op == '/':
            if b == 0:
                return None
            return a / b
    except Exception:
        return None
    return None

def path_to_str(path: Tuple[Union[str,int], ...]) -> str:
    out = "root"
    for p in path:
        if isinstance(p, int):
            out += f"[{p}]"
        else:
            out += f'["{p}"]'
    return out

def walk_and_fix(obj: Any, path: Tuple = ()) -> Tuple[List[dict], List[str]]:
    issues = []
    test_key_paths = []
    if isinstance(obj, dict):
        for key in obj.keys():
            if 'test' in key.lower():
                test_key_paths.append(path + (key,))
        if 'question' in obj and 'answer' in obj:
            q = obj.get('question')
            provided = obj.get('answer')
            computed = eval_simple(q) if isinstance(q, str) else None
            need_fix = False
            reason = None
            if computed is None:
                reason = "nieparsowalne pytanie"
            else:
                if provided is None:
                    need_fix = True
                    reason = "brak odpowiedzi"
                else:
                    try:
                        if abs(computed - float(provided)) > 1e-9:
                            need_fix = True
                            reason = f"niezgodna odpowiedź ({provided} vs {computed})"
                    except Exception:
                        need_fix = True
                        reason = "nieprawidłowy typ odpowiedzi"
            if need_fix and computed is not None:
                if computed.is_integer():
                    obj['answer'] = int(computed)
                else:
                    obj['answer'] = computed
                issues.append({
                    'path': path,
                    'kind': 'question-answer',
                    'question': q,
                    'old': provided,
                    'new': obj['answer'],
                    'reason': reason,
                })
        if 'q' in obj and 'a' in obj:
            q = obj.get('q')
            provided = obj.get('a')
            if provided is None or (isinstance(provided, str) and provided.strip() == ""):
                issues.append({
                    'path': path,
                    'kind': 'q-a',
                    'question': q,
                    'old': provided,
                    'new': None,
                    'reason': 'brak odpowiedzi',
                })
        for k, v in obj.items():
            sub_issues, sub_tests = walk_and_fix(v, path + (k,))
            issues.extend(sub_issues)
            test_key_paths.extend(sub_tests)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            sub_issues, sub_tests = walk_and_fix(item, path + (idx,))
            issues.extend(sub_issues)
            test_key_paths.extend(sub_tests)
    return issues, test_key_paths

def try_parse_json(raw: str) -> Any:
    cleaned = TRAILING_COMMA_BEFORE_CLOSER.sub(lambda m: m.group('closer'), raw)
    return json.loads(cleaned)

def fallback_linebyline_fix(text: str) -> Tuple[str, List[dict], List[str]]:
    
    issues = []
    test_lines = []
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.search(r'"test"', line, re.IGNORECASE) or re.search(r'"test[-_a-z]*"', line, re.IGNORECASE):
            test_lines.append(f"linia {i+1}: {line.strip()}")
        q_match = re.search(r'"question"\s*:\s*"([^"]+)"', line)
        if q_match:
            question = q_match.group(1)
            j = i + 1
            answer_idx = None
            provided_raw = None
            while j < len(lines) and not re.search(r'[}\]]', lines[j]):
                a_match = re.search(r'"answer"\s*:\s*([^\s,}]+)', lines[j])
                if a_match:
                    answer_idx = j
                    provided_raw = a_match.group(1)
                    break
                j += 1
            computed = eval_simple(question)
            if answer_idx is not None:
                if computed is not None:
                    try:
                        provided_val = float(provided_raw.strip().rstrip(','))
                        if abs(computed - provided_val) > 1e-9:
                            new_val = int(computed) if computed.is_integer() else computed
                            comma = ',' if lines[answer_idx].strip().endswith(',') else ''
                            lines[answer_idx] = re.sub(r'"answer"\s*:\s*[^\s,}]+',
                                                       f'"answer": {new_val}', lines[answer_idx])
                            if comma and not lines[answer_idx].strip().endswith(','):
                                lines[answer_idx] = lines[answer_idx].rstrip('\n') + ',' + '\n'
                            issues.append({
                                'linia': answer_idx + 1,
                                'kind': 'question-answer',
                                'question': question,
                                'old': provided_raw,
                                'new': new_val,
                                'reason': f'niezgodna odpowiedź ({provided_raw} vs {computed})',
                            })
                    except Exception:
                        pass  
                else:
                    issues.append({
                        'linia': i + 1,
                        'kind': 'question-answer',
                        'question': question,
                        'old': provided_raw,
                        'new': None,
                        'reason': 'nieparsowalne pytanie',
                    })
            else:
                if computed is not None:
                    new_val = int(computed) if computed.is_integer() else computed
                    insertion = f'    "answer": {new_val},\n'
                    lines.insert(i + 1, insertion)
                    issues.append({
                        'linia': i + 2,
                        'kind': 'question-answer',
                        'question': question,
                        'old': None,
                        'new': new_val,
                        'reason': 'brak odpowiedzi, wstawiono',
                    })
        i += 1
    return ''.join(lines), issues, test_lines

def process_file(input_path: Union[str, Path], output_path: Union[str, Path]):
    input_path = Path(input_path)
    output_path = Path(output_path)
    raw = input_path.read_text(encoding='utf-8')

    print("Próba parsowania jako JSON (z usunięciem trailing commas)...")
    parsed = None
    issues = []
    test_key_paths = []

    try:
        data = try_parse_json(raw)
        parsed = True
        issues, test_key_paths = walk_and_fix(data)
        with output_path.open('w', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
        print(f"Użyto trybu JSON. Znaleziono / poprawiono {len(issues)} wpisów.")
        for idx, iss in enumerate(issues, 1):
            print(f"{idx}. {path_to_str(iss['path'])} | {iss['kind']} | pytanie: {iss['question']} | "
                  f"stare: {iss['old']} | nowe: {iss['new']} | {iss['reason']}")
        if test_key_paths:
            print("\nŚcieżki z kluczami zawierającymi 'test':")
            for p in sorted({path_to_str(p) for p in test_key_paths}):
                print(" -", p)
        else:
            print("\nNie znaleziono kluczy zawierających 'test'.")
    except Exception as e:
        print("Parsowanie JSON nie powiodło się (źle sformatowany). Włączam fallback liniowy.")
        fixed_text, fallback_issues, test_lines = fallback_linebyline_fix(raw)
        output_path.write_text(fixed_text, encoding='utf-8')
        print(f"Fallback: zmodyfikowano {len(fallback_issues)} wpisów.")
        for idx, iss in enumerate(fallback_issues, 1):
            print(f"{idx}. linia {iss.get('linia')} | {iss['kind']} | pytanie: {iss['question']} | "
                  f"stare: {iss['old']} | nowe: {iss['new']} | {iss['reason']}")
        if test_lines:
            print("\nWykryte miejsca z 'test' (linia i zawartość):")
            for tl in test_lines:
                print(" -", tl)
        else:
            print("\nNie znaleziono 'test' w tekście.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Naprawa question/answer w pliku JSON-like (txt) i wykrywanie 'test'.")
    parser.add_argument("input", help="ścieżka do wejściowego pliku (.txt lub .json)")
    parser.add_argument("output", help="ścieżka do zapisu poprawionego pliku")
    args = parser.parse_args()
    process_file(args.input, args.output)

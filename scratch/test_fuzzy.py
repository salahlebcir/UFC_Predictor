import sys
import unicodedata
import re
import difflib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}

def normalize_fighter_name(name):
    if not name: return ''
    nfkd = unicodedata.normalize('NFD', str(name))
    ascii_str = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    clean = re.sub(r'[\"\\\'].*?[\"\\\']', ' ', ascii_str.lower())
    clean = re.sub(r'[^\w\s]', ' ', clean)
    tokens = [t for t in clean.split() if t not in suffixes]
    return ' '.join(tokens)

def fuzzy_match_fighter_name(name, targets, threshold=0.75):
    if not name or not targets: return None
    norm_q = normalize_fighter_name(name)
    if not norm_q: return None
    
    # 1. Exact match on normalized string
    for t in targets:
        if normalize_fighter_name(t) == norm_q:
            return t
            
    q_tokens = norm_q.split()
    if not q_tokens: return None
    q_last = q_tokens[-1]
    
    best_t = None
    best_score = 0.0
    
    for t in targets:
        norm_t = normalize_fighter_name(t)
        t_tokens = norm_t.split()
        if not t_tokens: continue
        t_last = t_tokens[-1]
        
        # Check token set match (e.g. 'ian garry' in 'ian machado garry')
        set_q = set(q_tokens)
        set_t = set(t_tokens)
        if set_q.issubset(set_t) or set_t.issubset(set_q):
            return t
            
        # Last name MUST have significant overlap or match
        last_ratio = difflib.SequenceMatcher(None, q_last, t_last).ratio()
        if last_ratio >= 0.70 or (len(q_last) >= 4 and q_last in norm_t) or (len(t_last) >= 4 and t_last in norm_q):
            overall_ratio = difflib.SequenceMatcher(None, norm_q, norm_t).ratio()
            if overall_ratio >= threshold and overall_ratio > best_score:
                best_score = overall_ratio
                best_t = t
                
    return best_t

# Test valid matches
print('Steve Erceg vs Stephen Erceg:', fuzzy_match_fighter_name('Steve Erceg', ['Stephen Erceg']))
print('Ian Machado Garry vs Ian Garry:', fuzzy_match_fighter_name('Ian Machado Garry', ['Ian Garry']))
print('Edson Barboza Jr. vs Edson Barboza:', fuzzy_match_fighter_name('Edson Barboza Jr.', ['Edson Barboza']))
print('Uros Medic vs Uroš Medić:', fuzzy_match_fighter_name('Uros Medic', ['Uroš Medić']))

# Test false positives prevention
print('Magomed Zaynukov vs Magomed Ankalaev:', fuzzy_match_fighter_name('Magomed Zaynukov', ['Magomed Ankalaev']))
print('Abubakar Vagaev vs Abubakar Nurmagomedov:', fuzzy_match_fighter_name('Abubakar Vagaev', ['Abubakar Nurmagomedov']))
print('Muhammad Said vs Muhammad Naimov:', fuzzy_match_fighter_name('Muhammad Said', ['Muhammad Naimov']))

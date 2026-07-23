"""
Module d'utilitaires génériques et universels pour UFC Fight Predictor V3.
Réalise la normalisation Unicode (suppression des accents/diacritiques),
le nettoyage des suffixes (Jr., Sr., II, III) et le matching tolérant par jetons (Token Set Match) et SequenceMatcher.
Vérifie la concordance du nom de famille pour éviter les faux positifs sur les prénoms communs (ex: Magomed, Abubakar, Muhammad).
"""

import re
import unicodedata
import difflib

# Suffixes génériques à exclure lors de la comparaison
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize_fighter_name(name: str) -> str:
    """
    Normalise un nom de combattant de manière universelle :
    1. Suppression des diacritiques/accents Unicode (ex: Uroš Medić -> uros medic, Mateusz Rębecki -> mateusz rebecki)
    2. Suppression des surnoms entre guillemets ("...")
    3. Suppression des suffixes (Jr., Sr., II, III), de la ponctuation et conversion en minuscules
    """
    if not name:
        return ""

    # Normalisation NFD pour isoler les caractères d'accentuation
    nfkd_form = unicodedata.normalize("NFD", str(name))
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    # Nettoyage des surnoms ("The Last Stylebender")
    clean = re.sub(r"[\"'].*?[\"']", " ", only_ascii.lower())

    # Remplacement de la ponctuation par des espaces
    clean = re.sub(r"[^\w\s]", " ", clean)

    # Invalidation des suffixes
    tokens = [t for t in clean.split() if t not in SUFFIXES]

    return " ".join(tokens)


def is_token_set_match(name1: str, name2: str) -> bool:
    """
    Vérifie la concordance entre deux noms via inclusion de jetons (Token Set Match).
    Exemple : Ian Machado Garry vs Ian Garry -> True
    """
    norm1 = normalize_fighter_name(name1)
    norm2 = normalize_fighter_name(name2)

    if not norm1 or not norm2:
        return False

    if norm1 == norm2:
        return True

    t1 = set(norm1.split())
    t2 = set(norm2.split())

    if not t1 or not t2:
        return False

    # Sous-ensemble exact de mots (short name vs full composite name)
    if t1.issubset(t2) or t2.issubset(t1):
        return True

    return False


def fuzzy_match_fighter_name(name: str, targets: list, threshold: float = 0.75) -> str:
    """
    Recherche tolérante et universelle d'un nom parmi une liste de cibles :
    1. Concordance exacte sur la chaîne normalisée NFD
    2. Token Set Match (ex: Ian Machado Garry vs Ian Garry, Edson Barboza Jr. vs Edson Barboza)
    3. Matching par nom de famille (dernier token) + SequenceMatcher générique (>= threshold)
    Empêche les faux positifs sur prénoms communs (ex: Magomed, Abubakar, Muhammad).
    """
    if not name or not targets:
        return None

    norm_q = normalize_fighter_name(name)
    if not norm_q:
        return None

    # 1. Matching exact ou normalisé direct
    for t in targets:
        if normalize_fighter_name(t) == norm_q:
            return t

    q_tokens = norm_q.split()
    if not q_tokens:
        return None
    q_last = q_tokens[-1]

    best_t = None
    best_score = 0.0

    for t in targets:
        norm_t = normalize_fighter_name(t)
        t_tokens = norm_t.split()
        if not t_tokens:
            continue
        t_last = t_tokens[-1]

        # 2. Token set match (ex: 'ian garry' in 'ian machado garry')
        set_q = set(q_tokens)
        set_t = set(t_tokens)
        if set_q.issubset(set_t) or set_t.issubset(set_q):
            return t

        # 3. Validation par nom de famille (le nom de famille doit être similaire ou contenu)
        last_ratio = difflib.SequenceMatcher(None, q_last, t_last).ratio()
        if last_ratio >= 0.70 or (len(q_last) >= 4 and q_last in norm_t) or (len(t_last) >= 4 and t_last in norm_q):
            overall_ratio = difflib.SequenceMatcher(None, norm_q, norm_t).ratio()
            if overall_ratio >= threshold and overall_ratio > best_score:
                best_score = overall_ratio
                best_t = t

    return best_t

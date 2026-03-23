import pickle
import os
from rapidfuzz import fuzz
from transliterate import translit
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "../ai/ai_model.pkl")

with open(MODEL_PATH, "rb") as f:
    model_data = pickle.load(f)

model = model_data["model"]
vectorizer = model_data["vectorizer"]

def normalize(text: str):
    return text.lower().strip()


def normalize_with_translit(text: str):
    original = normalize(text)

    try:
        translit_text = translit(original, "ru", reversed=True)
    except Exception:
        translit_text = original

    return original, normalize(translit_text)

def build_brand_dict(goods):
    candidates = []

    for item in goods:
        first_word = item["name"].split()[0].lower()
        candidates.append(first_word)

    counter = Counter(candidates)

    brands = set()

    for brand, count in counter.items():
        if count >= 1:
            brands.add(brand)

    return brands

def ai_search(query: str, goods: list, top_k: int | None = None):

    BRANDS = build_brand_dict(goods)
    CATEGORIES = set(normalize(g["category"]) for g in goods)

    query_original, query_translit = normalize_with_translit(query)

    query_versions = [query_original, query_translit]

    names = [normalize(g["name"]) for g in goods]

    X = vectorizer.transform(names)
    ml_probs = model.predict_proba(X)[:, 1]

    results = []

    for i, item in enumerate(goods):

        name_original, name_translit = normalize_with_translit(item["name"])
        name_versions = [name_original, name_translit]

        fuzzy_score = max(
            fuzz.partial_ratio(q, n) / 100
            for q in query_versions
            for n in name_versions
        )

        category_score = category_match_score(query, item["category"])

        ml_prob = ml_probs[i]

        score = (
            0.35 * fuzzy_score +
            0.25 * ml_prob +
            0.40 * category_score
        )

        if score > 0.55:
            results.append({
                "item": item,
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)

    if top_k:
        results = results[:top_k]

    return results

def category_match_score(query, category):
    q = normalize(query)
    c = normalize(category)

    # точное совпадение
    if q == c: return 1.0

    # частичное совпадение
    if q in c or c in q: return 0.9

    # fuzzy совпадение
    score = fuzz.partial_ratio(q, c) / 100

    if score > 0.7: return score

    # совпадение слов
    q_words = set(q.split())
    c_words = set(c.split())

    if q_words & c_words: return 0.6

    return 0
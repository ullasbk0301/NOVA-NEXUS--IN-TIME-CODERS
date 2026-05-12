import requests
import json
import re
from datetime import datetime, timedelta
from rapidfuzz import process

# =============================
# DICTIONARIES
# =============================
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12
}

ABBREVIATIONS = {
    "bt": "bluetooth",
    "wnt": "want",
    "plz": "please",
    "pls": "please",
    "ur": "your",
    "u": "you",
    "mnth": "month",
    "wk": "week",
    "hp": "harry potter",
    "lptp": "laptop",
    "phn": "phone",
    "tmrw": "tomorrow",
    "witin": "within",
    "nxt": "next"
}

MONTH_ALIASES = {
    "jan": "january", "feb": "february", "mar": "march",
    "apr": "april", "may": "may", "jun": "june",
    "jul": "july", "aug": "august", "sep": "september",
    "oct": "october", "nov": "november", "dec": "december"
}

MONTH_NAMES = set(MONTH_ALIASES.values())
MONTH_PATTERN = "|".join(MONTH_NAMES)

COMMON_WORDS = [
    "watch", "piano", "pencil", "phone", "laptop",
    "book", "pen", "chair", "table", "keyboard",
    "speaker", "bluetooth", "harry potter", "scissors"
]

ORDER_WORDS = {
    "i", "want", "need", "please", "order", "book", "get", "me",
    "a", "an", "the", "within", "with", "by", "before", "on", "for",
    "next", "week", "month", "day"
}

# =============================
# DATE VALIDATION (OPTIONAL USE)
# =============================
def is_valid_date(date_str):

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.today().date()
        return date_obj.date() >= today
    except:
        return False

# =============================
# TEXT CLEANING
# =============================
def expand_abbreviations(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return " ".join([ABBREVIATIONS.get(w, w) for w in words])

def normalize_months(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return " ".join([MONTH_ALIASES.get(w, w) for w in words])

# =============================
# FUZZY CORRECTION
# =============================
def correct_words(text):

    words = text.lower().split()
    corrected = []

    for w in words:

        if w in ORDER_WORDS or w in NUMBER_WORDS or w in MONTH_NAMES or w.isdigit():
            corrected.append(w)
            continue

        match, score, _ = process.extractOne(w, COMMON_WORDS)

        if score >= 90:
            corrected.append(match)
        else:
            corrected.append(w)

    return " ".join(corrected)

# =============================
# REMOVE DUPLICATES
# =============================
def remove_duplicate_words(text):

    seen = set()
    result = []

    for w in text.split():
        if w not in seen:
            seen.add(w)
            result.append(w)

    return " ".join(result)

# =============================
# CLEAN DATE PHRASES
# =============================
def remove_date_phrases(text):

    text = re.sub(r'\b(today|tomorrow|next week)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(within|by|before|on)\b', '', text, flags=re.IGNORECASE)

    return text

# =============================
# QUANTITY
# =============================
def extract_quantity(text):

    for w in text.lower().split():
        if w in NUMBER_WORDS:
            return NUMBER_WORDS[w]

    nums = re.findall(r'\b\d+\b', text)
    if nums:
        return int(nums[0])

    return 1

# =============================
# SMART DEADLINE FIX (FINAL)
# =============================
def extract_deadline(text):

    text = normalize_months(expand_abbreviations(text))
    today = datetime.today()

    # ---------------------
    # RELATIVE DATES
    # ---------------------
    if "next week" in text:
        return (today + timedelta(days=7)).strftime("%Y-%m-%d")

    if "tomorrow" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # ---------------------
    # ABSOLUTE DATE MATCH
    # ---------------------
    match = re.search(rf'\b(\d{{1,2}})\s+({MONTH_PATTERN})\b', text)

    if not match:
        match = re.search(rf'\b({MONTH_PATTERN})\s+(\d{{1,2}})\b', text)

    if match:

        try:
            if match.group(1).isdigit():
                day = int(match.group(1))
                month = match.group(2)
            else:
                day = int(match.group(2))
                month = match.group(1)

            # TRY CURRENT YEAR FIRST
            date_obj = datetime.strptime(
                f"{day} {month} {today.year}",
                "%d %B %Y"
            )

            # IF PAST → MOVE TO NEXT YEAR (FIX)
            if date_obj.date() < today.date():
                date_obj = datetime.strptime(
                    f"{day} {month} {today.year + 1}",
                    "%d %B %Y"
                )

            return date_obj.strftime("%Y-%m-%d")

        except:
            return "Not specified"

    return "Not specified"

# =============================
# PIPELINE
# =============================
def fallback_extract(text):

    text = expand_abbreviations(text)
    text = normalize_months(text)

    quantity = extract_quantity(text)
    deadline = extract_deadline(text)

    text = correct_words(text)
    text = remove_date_phrases(text.lower())
    text = remove_duplicate_words(text)
    text = re.sub(r'\d+', '', text)

    words = [
        w for w in text.split()
        if w and w not in ORDER_WORDS and w not in NUMBER_WORDS and w not in MONTH_NAMES
    ]

    item_name = " ".join(words[:3]).title() if words else "Item"

    if any(x in item_name.lower() for x in ["watch", "phone", "speaker", "bluetooth", "laptop"]):
        category = "Electronics"
    elif any(x in item_name.lower() for x in ["pen", "pencil", "book", "scissors"]):
        category = "Stationery"
    else:
        category = "General"

    return {
        "items": [{
            "name": item_name,
            "category": category,
            "quantity": quantity
        }],
        "deadline": deadline
    }

# =============================
# MAIN FUNCTION
# =============================
def llm_extract(text):

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi",
                "prompt": text,
                "stream": False
            }
        )

        result = response.json()["response"]

        try:
            return json.loads(result)
        except:
            return fallback_extract(text)

    except:
        return fallback_extract(text)
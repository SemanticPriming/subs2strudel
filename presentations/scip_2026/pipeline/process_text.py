"""
Step 3: process model output the way the human answers were processed.

The rules are copied from the FLT-Projects notebooks (github.com/doomlab/FLT-Projects):
  01 clean and lowercase, 02 expand contractions, 04 expand abbreviations,
  05 spaCy lemmas, 06 spell out numbers, 07 tidy odd tokens and remove stop
  words and the cue word, 08 one word per row (a repeated word kept once).
Spelling (03) is skipped for model output. Cues that are themselves stop words
keep their stop words, as in the human pipeline.

process_answer(cue, text) -> list of (position, word, original_word, pos)
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd
import spacy
from num2words import num2words

INPUTS = Path(__file__).resolve().parent.parent / "results" / "inputs"
STOP = set(INPUTS.joinpath("stopwords.txt").read_text().split())
EXEMPT = set(pd.read_csv(INPUTS / "exempt_cues.csv")["cue"])
FRAGMENTS = {"d", "t", "s", "m", "re", "ll", "ve", "y", "o", "ma"}
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

QUOTES = {"\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'", "`": "'", "\u00b4": "'",
          "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u2013": "-", "\u2014": "-"}

def clean_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\\'", "'").replace('\\"', '"')  # escaped quotes left over from the export
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)  # stray control characters
    for old, new in QUOTES.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text)  # line breaks, tabs, repeated spaces
    return text.strip().lower()

legacy = pd.read_csv(INPUTS / "contraction_dict.csv")
CONTRACTIONS = dict(zip(legacy["contraction"].str.lower(), legacy["expanded"].str.lower()))

# the legacy dictionary leaves some irregular forms out
CONTRACTIONS.update({"won't": "will not", "can't": "can not", "cannot": "can not", "y'all": "you all", "ma'am": "madam"})

WORD = re.compile(r"[a-z]+(?:'[a-z]+)+'?|[a-z]+s'")  # tokens that contain an apostrophe

CONTRACTION_RULES = [("n't", " not"), ("'re", " are"), ("'ve", " have"), ("'ll", " will"), ("'m", " am"), ("'d", " would")]


def _expand_token(tok):
    if tok == "one's":
        return ""
    if tok in CONTRACTIONS:
        new = CONTRACTIONS[tok]
    else:
        new = tok
        for suffix, repl in CONTRACTION_RULES:
            if tok.endswith(suffix):
                new = tok[: -len(suffix)] + repl
                break
        else:
            if tok.endswith("'s"):
                new = tok[:-2]          # possessive
            elif tok.endswith("s'"):
                new = tok[:-1]          # plural possessive
    return new

def expand_contractions(text):
    return WORD.sub(lambda m: _expand_token(m.group(0)), text)

# (name, pattern, replacement); a trailing period belongs to the abbreviation and is removed with it
NUM = r"(?<=\d)\s*|(?<=\d\s)"   # after a number, with or without a space
ABBREV_RULES = [
    ("dr",     r"\bdr\b\.?",                       "doctor"),
    ("mr",     r"\bmr\b\.?",                       "mister"),
    ("mrs",    r"\bmrs\b\.?",                      "missus"),
    ("jr",     r"\bjr\b\.?",                       "junior"),
    ("sr",     r"\bsr\b\.?",                       "senior"),
    ("rd",     r"\brd\b\.?",                       "road"),
    ("ave",    r"\bave\b\.?",                      "avenue"),
    ("blvd",   r"\bblvd\b\.?",                     "boulevard"),
    ("st_saint",  r"\bst\b\.?(?=\s+[a-z])",        "saint"),
    ("st_street", r"\bst\b\.?",                     "street"),
    ("fl_oz",  r"\bfl\.?\s*oz\b\.?",              "fluid ounce"),
    ("oz",     r"(?<=\d)\s*oz\b\.?|(?<=\d )oz\b\.?", " ounce"),
    ("lbs",    r"\blbs\b\.?",                      "pounds"),
    ("lb",     r"\blb\b\.?",                       "pound"),
    ("ft_fort", r"\bft\b\.?(?=\s+[a-z])",         "fort"),
    ("ft_feet", r"(?<=\d)\s*ft\b\.?|(?<=\d )ft\b\.?", " feet"),
    ("mph",    r"\bmph\b",                          "miles per hour"),
    ("tv",     r"\btv\b\.?",                       "television"),
    ("bbq",    r"\bbbq\b",                          "barbecue"),
    ("dept",   r"\bdept\b\.?",                     "department"),
    ("approx", r"\bapprox\b\.?",                   "approximately"),
    ("avg",    r"\bavg\b\.?",                      "average"),
]
COMPILED = [(name, re.compile(pat), rep) for name, pat, rep in ABBREV_RULES]

def expand_abbreviations(text):
    for name, pat, rep in COMPILED:
        text = pat.sub(rep, text)
    return text

# nouns that are only used in the plural: the singular means something else, so keep them as written
KEEP_AS_WRITTEN = {
    "clothes", "pants", "glasses", "jeans", "shorts", "scissors", "stairs", "species", "politics",
    "mathematics", "athletics", "ethics", "physics", "economics", "goggles", "tights", "trousers",
    "pliers", "headquarters", "crossroads", "outskirts", "belongings", "savings", "earnings",
}

def lemma_of(t):
    return t.text.lower() if t.text.lower() in KEEP_AS_WRITTEN else t.lemma_.lower()



FRACTIONS = {"1/2": "one half", "1/3": "one third", "2/3": "two thirds", "1/4": "one quarter", "3/4": "three quarters"}

def words(n, **kwargs):
    text = num2words(n, **kwargs).replace("-", " ").replace(",", "")
    return " ".join(w for w in text.split() if w != "and")

def spell(token):
    """Returns the number written as words, or None if the token is not a plain number."""
    t = token.lower()
    if t in FRACTIONS:
        return FRACTIONS[t]
    if re.fullmatch(r"\d{1,3}(,\d{3})+|\d+", t):                 # 4, 1,000, 5280
        n = int(t.replace(",", ""))
        if "," not in t and 1100 <= n <= 2099 and n % 1000 != 0:   # years
            return words(n, to="year")
        return words(n)
    m = re.fullmatch(r"(\d+)(st|nd|rd|th)", t)                      # 1st, 25th
    if m:
        return words(int(m.group(1)), to="ordinal")
    if re.fullmatch(r"\d+\.\d+", t):                                # 3.5
        whole, frac = t.split(".")
        return words(int(whole)) + " point " + " ".join(words(int(d)) for d in frac)
    m = re.fullmatch(r"(\d+)/(\d+)", t)                            # 9/11, 20/20
    if m:
        return words(int(m.group(1))) + " " + words(int(m.group(2)))
    m = re.fullmatch(r"(\d{2}|\d{4})s", t)                         # 50s, 1950s
    if m:
        return decade(int(m.group(1)))
    return None

def decade(n):
    text = words(n, to="year") if n >= 1000 else words(n)
    return re.sub(r"y$", "ies", text) if n % 100 else text + 's'

def tidy(word):
    """One token in, a list of clean words out (can be empty)."""
    word = word.lower().replace("_", " ").replace("/", " ")
    word = re.sub(r"(?<=[a-z])\.(?=[a-z])", "", word)       # u.s -> us
    word = word.replace(".", " ").replace("'", "")           # i.e. -> i e ; o'clock -> oclock
    if re.search(r"\d", word):                                 # h2o, k-12, 12:00: only trim the edges
        return [p.strip(" -,;:") for p in word.split() if re.search(r"[a-z0-9]", p)]
    parts = re.split(r"[\s\-,;:!?\x22()\[\]{}]+", word)
    return [p for p in parts if re.search(r"[a-z]", p)]



_cue_lemma_cache = {}


def _cue_lemma(cue):
    if cue not in _cue_lemma_cache:
        _cue_lemma_cache[cue] = " ".join(t.lemma_.lower() for t in nlp(cue))
    return _cue_lemma_cache[cue]


def _lemma_of(t):
    return t.text.lower() if t.text.lower() in KEEP_AS_WRITTEN else t.lemma_.lower()


def process_answer(cue, text):
    """One answer in, a list of (position, word, original_word, pos) out."""
    text = expand_abbreviations(expand_contractions(clean_text(text)))
    words = [t for t in nlp(text) if not (t.is_punct or t.is_space)]
    own = {cue, _cue_lemma(cue)}
    keep_all = cue in EXEMPT
    items = []
    for t in words:
        original, lemma, pos = t.text, _lemma_of(t), t.pos_
        spelled = spell(original)
        pieces = [(original, w, "NUM") for w in spelled.split()] if spelled is not None else [(original, lemma, pos)]
        for orig, lem, p in pieces:
            for w in tidy(lem):
                if w in own or orig.lower() in own or w in FRAGMENTS:
                    continue
                if not keep_all and (w in STOP or orig.lower() in STOP):
                    continue
                items.append((orig, w, p))
    out, seen = [], set()
    for orig, w, p in items:
        if w in seen:
            continue
        seen.add(w)
        out.append((len(out) + 1, w, orig, p))
    return out

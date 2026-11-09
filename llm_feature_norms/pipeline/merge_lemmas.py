"""
Merge related words into one lemma (step 12 of the FLT pipeline; also used by the LLM pipeline).

merge(word) applies, in this order:
  1. the 2019 translation (translation_2019.csv: word -> root, 7,522 words), minus the pairs
     that change the meaning (see `plausible`): opposites (happy/unhappy), function-word roots
     (sometimes/some), different words (medicine/medic, death/dead). A short list of sensible
     irregular pairs is always kept (lemma_force_merge.csv: people/person, grey/gray);
  2. if the 2019 data already saw the word and left it alone, or it is on the
     keep-separate list: no change;
  3. otherwise the affix rules from the 2019 affix list (-ness, -ous, -ful, -ive, -ion,
     -ment, -er, -ly, -ing, -ed, ...): strip an ending, accept the base only when it is a
     known root (lemma_roots.csv: 2019 roots plus words at least 5 people wrote) and
     WordNet says the two words are related (derivational link, or its root for
     inflected forms). If several bases fit, the most common one wins.
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd
from nltk.corpus import wordnet as wn

SUFFIXES = [("ness", ""), ("ments", ""), ("ment", ""), ("ation", "ate"), ("ation", ""), ("ation", "e"), ("tion", "te"),
            ("ion", ""), ("ion", "e"), ("ity", ""), ("ity", "e"), ("ous", ""), ("ious", "y"), ("ful", ""), ("less", ""),
            ("ive", ""), ("ive", "e"), ("ative", "ate"), ("al", ""), ("ial", ""), ("ic", ""), ("ly", ""), ("ily", "y"),
            ("y", ""), ("y", "e"), ("able", ""), ("able", "e"), ("ible", ""), ("ize", ""), ("ise", ""), ("ish", ""),
            ("ship", ""), ("dom", ""), ("er", ""), ("er", "e"), ("or", ""), ("ist", ""), ("ian", ""), ("ence", ""),
            ("ent", ""), ("ant", ""), ("ance", ""), ("ary", ""), ("en", ""), ("ing", ""), ("ing", "e"), ("ed", ""),
            ("ed", "e"), ("ies", "y"), ("ied", "y"), ("es", ""), ("s", "")]


NEGATIVE_PREFIXES = ("un", "in", "im", "il", "ir", "dis", "non", "mis", "anti", "ab", "de", "counter")
FUNCTION_WORDS = {"some", "with", "up", "out", "toward", "one", "the", "a", "an", "i", "it", "he", "be", "do", "have",
                  "all", "any", "no", "so", "on", "in", "at", "by", "of", "to"}
TRANSPARENT = [("ful", ""), ("ness", ""), ("ing", ""), ("ing", "e"), ("ed", ""), ("ed", "e"), ("s", ""), ("es", ""),
               ("ies", "y"), ("ied", "y"), ("ly", ""), ("ily", "y"), ("less", "")]


def _opposite(w, t):
    """The word is the root with a negating prefix (unhappy/happy): merging would join opposites."""
    for p in NEGATIVE_PREFIXES:
        if w.startswith(p) and len(w) > len(p) + 2:
            rest = w[len(p):]
            if rest == t or t.startswith(rest[:4]) or rest.startswith(t[:4]):
                return True
    return False


def _transparent(w, t):
    for suffix, rep in TRANSPARENT:
        if w.endswith(suffix):
            b = w[: -len(suffix)] + rep
            if b == t or (len(b) > 1 and b[-1] == b[-2] and b[:-1] == t):
                return True
    return False


class Merger:
    def __init__(self, folder):
        folder = Path(folder)
        t = pd.read_csv(folder / "translation_2019.csv", keep_default_na=False)
        self.table = dict(zip(t["word"], t["merge_to"]))
        self.seen = set(Path(folder / "translation_2019_seen.txt").read_text().split())
        self.keep = set(pd.read_csv(folder / "lemma_keep_separate.csv", keep_default_na=False)["word"])
        r = pd.read_csv(folder / "lemma_roots.csv", keep_default_na=False)
        self.roots = dict(zip(r["word"], r["count"].astype(int)))
        self._cache = {}
        force = pd.read_csv(folder / "lemma_force_merge.csv", keep_default_na=False)
        self.force = dict(zip(force["word"], force["merge_to"]))
        # the 2019 pairs we do not merge (meaning changes); kept so they are not re-merged by the affix rules
        self.rejected = {w: t for w, t in self.table.items() if w not in self.force and not self.plausible(w, t)}
        self.table = {w: t for w, t in self.table.items() if w not in self.rejected}

    @staticmethod
    @lru_cache(None)
    def _related(w):
        out = set()
        for syn in wn.synsets(w):
            for lem in syn.lemmas():
                if lem.name().lower() == w:
                    out.update(d.name().lower() for d in lem.derivationally_related_forms())
                    out.update(d.name().lower() for d in lem.pertainyms())
        for pos in "vna":
            m = wn.morphy(w, pos)
            if m:
                out.add(m)
        return out

    def plausible(self, w, t):
        """A 2019 pair is kept when it is not an opposite or function-word root, and the two words are
        related in WordNet or the word is the root plus a transparent ending (-ful, -ness, -ing, -ed, -s, -ly)
        on a common word."""
        if t in FUNCTION_WORDS or w in FUNCTION_WORDS or _opposite(w, t):
            return False
        if t in self._related(w) or w in self._related(t):
            return True
        return _transparent(w, t) and self.roots.get(t, 0) >= 50

    def _rule(self, w):
        best = None
        for suffix, rep in SUFFIXES:
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                base = w[: -len(suffix)] + rep
                for c in {base, base[:-1] if base[-1] == base[-2] else base}:
                    if c in self.roots and c != w and c not in FUNCTION_WORDS and not _opposite(w, c) and (c in self._related(w) or w in self._related(c)):
                        if best is None or self.roots[c] > self.roots[best]:
                            best = c
        return best

    def merge(self, w):
        if w not in self._cache:
            if w in self.force:
                out = self.force[w]
            elif w in self.table:
                out = self.table[w]
            elif w in self.seen or w in self.keep or w in self.rejected:
                out = w
            else:
                out = self._rule(w) or w
            self._cache[w] = out
        return self._cache[w]

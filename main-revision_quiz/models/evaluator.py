import difflib
import re
import unicodedata
from typing import List, Optional, Union

try:
    from rapidfuzz import fuzz

    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False


class AnswerEvaluator:
    # This dictionary maps number words to integers.
    # It was so annoying when users typed "three" and got marked wrong
    # because the answer was "3", so I built this to fix it!
    _WORD_NUMS = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
    }

    @staticmethod
    def normalize_text(s: str) -> str:
        """This cleans up whatever the user typed. It makes everything lowercase,
        removes weird punctuation, and normalises Unicode characters so comparisons don't break."""
        if s is None:
            return ""
        s = str(s)
        s = unicodedata.normalize("NFKC", s)
        s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        s = s.strip().lower()
        s = re.sub(r"[^0-9a-z\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def normalize_option(s: str) -> str:
        """get single option token like 'a' or '1' if it is present."""
        s = AnswerEvaluator.normalize_text(s)
        if not s:
            return ""
        parts = s.split()
        first = parts[0]
        m = re.match(r"^([a-zA-Z0-9])[\.\)]?$", first)
        if m:
            return m.group(1)
        return s

    @classmethod
    def word_number_to_int(cls, s: str) -> Optional[int]:
        """Convert simple word numbers like 'twenty one' to int, or None."""
        s = cls.normalize_text(s)
        if not s:
            return None
        parts = s.split()
        total = 0
        i = 0
        while i < len(parts):
            w = parts[i]
            if w in cls._WORD_NUMS:
                val = cls._WORD_NUMS[w]
                if (
                    val >= 20
                    and i + 1 < len(parts)
                    and parts[i + 1] in cls._WORD_NUMS
                    and cls._WORD_NUMS[parts[i + 1]] < 10
                ):
                    total += val + cls._WORD_NUMS[parts[i + 1]]
                    i += 2
                    continue
                total += val
                i += 1
            else:
                return None
        return total

    @classmethod
    def is_numeric(cls, s: str) -> Optional[float]:
        """Try float conversion or small word number conversion."""
        s_norm = cls.normalize_text(s)
        if not s_norm:
            return None
        try:
            return float(s_norm)
        except ValueError:
            pass
        wn = cls.word_number_to_int(s_norm)
        if wn is not None:
            return float(wn)
        return None

    @staticmethod
    def _fuzzy_ratio(a: str, b: str) -> float:
        """Returns a similarity score from 0 to 100.
        I try to use rapidfuzz because it's way faster, but it falls back to Python's difflib
        just in case the teacher's PC doesn't have rapidfuzz installed!"""
        try:
            if _HAS_RAPIDFUZZ and hasattr(fuzz, "token_sort_ratio"):
                return float(fuzz.token_sort_ratio(a, b))
        except Exception:
            pass
        return difflib.SequenceMatcher(None, a, b).ratio() * 100.0

    @classmethod
    def evaluate(
        cls, user_answer_raw: str, correct_answers_raw: List[str]
    ) -> tuple[bool, Optional[str]]:
        # This is the main evaluation pipeline.
        # It runs the user's string through all my different matching checks.
        user_norm = cls.normalize_text(user_answer_raw)
        user_option = cls.normalize_option(user_answer_raw)

        # 88% seems to be the sweet spot for catching minor typos without accepting completely wrong words.
        fuzzy_threshold = 88.0

        for ca_raw in correct_answers_raw:
            ca_norm = cls.normalize_text(ca_raw)
            ca_option = cls.normalize_option(ca_raw)

            # 1) Exact match (after getting rid of caps and punctuation)
            if user_norm and ca_norm and user_norm == ca_norm:
                return True, ca_raw

            # 2) Multiple choice check (e.g. they type "a)" instead of the full answer)
            if user_option and ca_option and user_option == ca_option:
                return True, ca_raw

            # 3) Check if they typed a number as a word vs a digit
            ua_num = cls.is_numeric(user_answer_raw)
            ca_num = cls.is_numeric(ca_raw)
            if ua_num is not None and ca_num is not None:
                if abs(ua_num - ca_num) < 1e-9:
                    return True, ca_raw

            # 4) Containment check: if the right answer is a small part of a big sentence they typed
            if ca_norm and ca_norm in user_norm:
                return True, ca_raw

            # 5) Finally, fuzzy matching for small spelling mistakes
            if ca_norm and user_norm:
                score = cls._fuzzy_ratio(user_norm, ca_norm)
                if score >= fuzzy_threshold:
                    return True, ca_raw

        # If it failed all the checks, they got it wrong :(
        return False, None

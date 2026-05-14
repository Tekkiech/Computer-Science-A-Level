import difflib
import os
import re
import unicodedata
from typing import List, Optional, Union

try:
    from rapidfuzz import fuzz

    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False

# Lazy-loaded SLM model
_slm_model = None


def _get_slm_model():
    global _slm_model
    if _slm_model is None:
        try:
            from llama_cpp import Llama

            # The model should be stored in the models/ directory
            model_dir = os.path.join(os.path.dirname(__file__))
            # Upgraded to 1.5B parameter model (~1.6 GB for Q8_0)
            model_filename = "qwen2.5-1.5b-instruct-q8_0.gguf"
            model_path = os.path.join(model_dir, model_filename)

            if not os.path.exists(model_path):
                # Auto-download from huggingface if missing (using huggingface_hub)
                print(
                    f"SLM model not found at {model_path}. Attempting to download (~1.6GB)..."
                )
                try:
                    from huggingface_hub import hf_hub_download

                    downloaded_path = hf_hub_download(
                        repo_id="Qwen/Qwen2.5-1.5B-Instruct-GGUF",
                        filename=model_filename,
                        local_dir=model_dir,
                    )
                    model_path = downloaded_path
                    print(f"Downloaded model to {model_path}")
                except Exception as dl_e:
                    print(f"Could not auto-download model: {dl_e}")
                    return None

            _slm_model = Llama(
                model_path=model_path,
                n_ctx=2048,  # Increased context window to prevent truncation
                verbose=False,
            )
            print("Loaded SLM model successfully.")
        except ImportError:
            print(
                "llama_cpp not installed. Run: pip install llama-cpp-python huggingface-hub"
            )
            pass
        except Exception as e:
            print(f"Error loading SLM model: {e}")
            pass
    return _slm_model


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
        # Keep +, -, . to support chemistry charges and decimals
        s = re.sub(r"[^0-9a-z\s\+\-\.]", " ", s)
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
    def generative_evaluation(
        cls, question: str, mark_scheme: str, student_answer: str
    ) -> tuple[bool, str, float]:
        """Evaluate a long answer using the local generative SLM."""
        llm = _get_slm_model()
        if llm is None:
            return False, "AI model not loaded.", 0.0

        prompt = f"""<|im_start|>system
You are an expert A-Level Computer Science examiner evaluating a student's answer against a mark scheme.

CRITICAL GRADING RULES:
1. Focus entirely on the semantic meaning and core logic.
2. Acronym expansions (e.g., "IDE" means "Integrated Development Environment") are perfectly CORRECT.
3. Common abbreviations (e.g., 'env' for 'environment', 'db' for 'database') and synonyms are CORRECT.
4. Never contradict yourself: if the student's answer is a valid variation of the mark scheme, it is CORRECT.

OUTPUT FORMAT:
Respond on a single line starting with exactly "CORRECT - " or "WRONG - " followed by a brief, logical justification.
<|im_end|>
<|im_start|>user
Question: {question}
Mark Scheme: {mark_scheme}
Student Answer: {student_answer}
<|im_end|>
<|im_start|>assistant
"""
        try:
            # Added temperature=0.1 to make the tiny model's output much more predictable and deterministic
            response = llm(prompt, max_tokens=100, stop=["<|im_end|>"], temperature=0.1)
            # Just take the first line in case it starts rambling
            text = response["choices"][0]["text"].strip().split("\n")[0]

            passed = text.upper().startswith("CORRECT")

            # Since this is a pass/fail LLM, we'll map CORRECT to 1.0 similarity and WRONG to 0.0 for GUI compatibility
            sim_score = 1.0 if passed else 0.0

            return passed, text, sim_score
        except Exception as e:
            print(f"Generative AI error: {e}")
            return False, "Error during AI evaluation.", 0.0

    @classmethod
    def get_semantic_threshold(cls, reference_text: str) -> float:
        """Determine threshold based on answer length guidelines."""
        # Flat 70% threshold for all questions
        return 0.70

    @classmethod
    def evaluate(
        cls,
        user_answer_raw: str,
        correct_answers_raw: List[str],
        question_text: str = "",
        use_semantic: bool = True,
    ) -> tuple[bool, Optional[str], dict]:
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
                return (
                    True,
                    ca_raw,
                    {"method": "exact", "semantic_score": 0.0},
                )

            # 2) Multiple choice check (e.g. they type "a)" instead of the full answer)
            if user_option and ca_option and user_option == ca_option:
                return (
                    True,
                    ca_raw,
                    {"method": "mcq", "semantic_score": 0.0},
                )

            # 3) Check if they typed a number as a word vs a digit
            ua_num = cls.is_numeric(user_answer_raw)
            ca_num = cls.is_numeric(ca_raw)
            if ua_num is not None and ca_num is not None:
                if abs(ua_num - ca_num) < 1e-9:
                    return (
                        True,
                        ca_raw,
                        {"method": "numeric", "semantic_score": 0.0},
                    )

            # 4) Containment check: if the right answer is a small part of a big sentence they typed
            if ca_norm and ca_norm in user_norm:
                return (
                    True,
                    ca_raw,
                    {"method": "containment", "semantic_score": 0.0},
                )

            # 5) Finally, fuzzy matching for small spelling mistakes
            if ca_norm and user_norm:
                score = cls._fuzzy_ratio(user_norm, ca_norm)
                if score >= fuzzy_threshold:
                    return (
                        True,
                        ca_raw,
                        {
                            "method": "fuzzy",
                            "score": score,
                            "semantic_score": 0.0,
                        },
                    )

        # 6) Generative Fallback
        if use_semantic and _get_slm_model() is not None:
            # For generative LLMs, we usually just pass all correct answers joined as the mark scheme
            mark_scheme = " OR ".join(correct_answers_raw)
            passed, explanation, sim_score = cls.generative_evaluation(
                question=question_text,
                mark_scheme=mark_scheme,
                student_answer=user_answer_raw,
            )

            print(f"[LLM Debug] Output: {explanation}")

            if passed:
                return (
                    True,
                    correct_answers_raw[0],
                    {
                        "method": "semantic",
                        "semantic_score": sim_score,
                        "explanation": explanation,
                    },
                )
            else:
                return (
                    False,
                    None,
                    {
                        "method": "semantic",
                        "semantic_score": sim_score,
                        "explanation": explanation,
                    },
                )

        # If it failed all the checks, they got it wrong :(
        return False, None, {"method": "none", "semantic_score": 0.0}

from __future__ import annotations

from dataclasses import dataclass
import html
import re

from bs4 import BeautifulSoup
from confusable_homoglyphs import confusables
import nltk
from nltk.corpus import stopwords as nltk_stopwords
from pymorphy3 import MorphAnalyzer
from simplemma import in_target_language, is_known, lemmatize
from stop_words import get_stop_words


TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+(?:['`’][0-9A-Za-zА-Яа-яЁё]+)*|[.,]")
LATIN_RE = re.compile(r"[A-Za-z]")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
ELLIPSIS_RE = re.compile(r"\.{2,}")
BBCODE_TAG_RE = re.compile(r"\[(?:/?[A-Za-z]+(?:=[^\]]*)?|/?\*)\]")
HTML_LIKE_TAG_RE = re.compile(r"<[A-Za-z][^>]*>|</[A-Za-z][^>]*>")
ANGLE_BRACKETS_RE = re.compile(r"[<>]")
WHITESPACE_RE = re.compile(r"\s+")

SCRIPT_ALIASES = {"LATIN", "CYRILLIC"}
PUNCTUATION_TOKENS = {",", "."}

try:
    nltk_stopwords.words("english")
except LookupError:
    nltk.download("stopwords", quiet=True)

ENGLISH_STOP_WORDS = set(nltk_stopwords.words("english")) | {"much"}
ENGLISH_STOP_WORDS -= {"no", "nor", "not"}
RUSSIAN_STOP_WORDS = set(get_stop_words("ru")) - {"не"}
STOP_WORDS = ENGLISH_STOP_WORDS | RUSSIAN_STOP_WORDS

# There is no lightweight service-oriented library for this exact API shape,
# so we keep only the standard RU<->EN layout map as glue code.
KEYBOARD_LATIN_TO_CYRILLIC = str.maketrans(
    "qwertyuiopasdfghjklzxcvbnm",
    "йцукенгшщзфывапролдячсмить",
)
KEYBOARD_CYRILLIC_TO_LATIN = str.maketrans(
    "йцукенгшщзфывапролдячсмить",
    "qwertyuiopasdfghjklzxcvbnm",
)


@dataclass(slots=True)
class NormalizationResult:
    normalized_query: str
    tokens: list[str]
    corrections_applied: list[str]


class QueryNormalizer:
    def __init__(self) -> None:
        self._morph = MorphAnalyzer()

    def normalize_for_classic(self, query: str) -> NormalizationResult:
        return self._normalize(
            query=query,
            remove_stopwords=True,
            lemmatize_tokens=True,
            preserve_punctuation=False,
        )

    def normalize_for_embedding(self, query: str) -> NormalizationResult:
        result = self._normalize(
            query=query,
            remove_stopwords=False,
            lemmatize_tokens=False,
            preserve_punctuation=True,
        )
        return NormalizationResult(
            normalized_query=result.normalized_query,
            tokens=[],
            corrections_applied=result.corrections_applied,
        )

    def _normalize(
        self,
        query: str,
        remove_stopwords: bool,
        lemmatize_tokens: bool,
        preserve_punctuation: bool,
    ) -> NormalizationResult:
        corrections: list[str] = []
        prepared_tokens: list[str] = []
        preprocessed_query = self._preprocess_query(query, corrections)

        for raw_token in self._tokenize(preprocessed_query):
            if raw_token in PUNCTUATION_TOKENS:
                if preserve_punctuation:
                    prepared_tokens.append(raw_token)
                continue

            cased_token = raw_token.casefold()
            if cased_token != raw_token:
                corrections.append(f"casefold:{raw_token}->{cased_token}")

            punct_normalized_tokens, punctuation_correction = self._normalize_punctuation_token(
                cased_token
            )
            if punctuation_correction is not None:
                corrections.append(punctuation_correction)

            for punct_normalized_token in punct_normalized_tokens:
                normalized_tokens, token_corrections = self._normalize_token(
                    punct_normalized_token
                )
                corrections.extend(token_corrections)

                for token in normalized_tokens:
                    if not token:
                        continue

                    if remove_stopwords and token in STOP_WORDS:
                        corrections.append(f"stopword:{token}")
                        continue

                    final_token = token
                    lemma_correction: str | None = None

                    if lemmatize_tokens:
                        final_token, lemma_correction = self._lemmatize_token(token)

                    if remove_stopwords and final_token in STOP_WORDS:
                        corrections.append(f"stopword:{final_token}")
                        continue

                    if lemma_correction is not None:
                        corrections.append(lemma_correction)

                    prepared_tokens.append(final_token)

        return NormalizationResult(
            normalized_query=self._render_normalized_query(prepared_tokens),
            tokens=prepared_tokens,
            corrections_applied=corrections,
        )

    def _tokenize(self, query: str) -> list[str]:
        return [match.group(0) for match in TOKEN_RE.finditer(query)]

    def _preprocess_query(self, query: str, corrections: list[str]) -> str:
        preprocessed = html.unescape(query)
        if preprocessed != query:
            corrections.append(f"html-unescape:{query}->{preprocessed}")

        bbcode_stripped = BBCODE_TAG_RE.sub(" ", preprocessed)
        if bbcode_stripped != preprocessed:
            corrections.append("bbcode-strip")
        preprocessed = bbcode_stripped

        if HTML_LIKE_TAG_RE.search(preprocessed):
            html_stripped = BeautifulSoup(preprocessed, "html.parser").get_text(" ", strip=False)
            if html_stripped != preprocessed:
                corrections.append("html-tag-strip")
            preprocessed = html_stripped

        angle_normalized = ANGLE_BRACKETS_RE.sub(" ", preprocessed)
        if angle_normalized != preprocessed:
            corrections.append("angle-bracket-normalize")
        preprocessed = angle_normalized

        whitespace_normalized = WHITESPACE_RE.sub(" ", preprocessed).strip()
        if whitespace_normalized != preprocessed.strip():
            corrections.append("whitespace-normalize")
        
        ellipsis_normalized = ELLIPSIS_RE.sub(".", whitespace_normalized)
        if ellipsis_normalized != whitespace_normalized:
            corrections.append("ellipsis-normalize")
        
        return ellipsis_normalized

    def _normalize_punctuation_token(self, token: str) -> tuple[list[str], str | None]:
        return [token], None

    def _normalize_token(self, token: str) -> tuple[list[str], list[str]]:
        corrections: list[str] = []
        pieces = self._normalize_mixed_script(token)

        if pieces != [token]:
            corrections.append(f"mixed-alphabet:{token}->{','.join(pieces)}")

        fixed_pieces: list[str] = []
        for piece in pieces:
            fixed_layout = self._maybe_fix_keyboard_layout(piece)
            if fixed_layout != piece:
                corrections.append(f"keyboard-layout:{piece}->{fixed_layout}")
            fixed_pieces.append(fixed_layout)

        return fixed_pieces, corrections

    def _normalize_mixed_script(self, token: str) -> list[str]:
        if not confusables.is_mixed_script(token):
            return [token]

        dominant_alias = self._dominant_script_alias(token)
        if dominant_alias is not None:
            converted = "".join(
                self._convert_confusable_char(char, dominant_alias)
                for char in token
            )
            if not confusables.is_mixed_script(converted):
                return [converted]

        return self._split_by_script(token)

    def _convert_confusable_char(self, char: str, target_alias: str) -> str:
        char_alias = self._script_alias(char)
        if char_alias in {target_alias, "COMMON"}:
            return char

        for candidate in confusables.confusables_data.get(char, []):
            glyph = candidate["c"]
            if len(glyph) == 1 and self._script_alias(glyph) == target_alias:
                return glyph

        return char

    def _maybe_fix_keyboard_layout(self, token: str) -> str:
        if token.isdigit():
            return token

        if self._contains_latin(token) and self._contains_cyrillic(token):
            return token

        if self._contains_latin(token):
            candidate = token.translate(KEYBOARD_LATIN_TO_CYRILLIC)
            if self._score_russian_token(candidate) >= self._score_english_token(token) + 0.75:
                return candidate

        if self._contains_cyrillic(token):
            candidate = token.translate(KEYBOARD_CYRILLIC_TO_LATIN)
            if self._score_english_token(candidate) >= self._score_russian_token(token) + 0.75:
                return candidate

        return token

    def _lemmatize_token(self, token: str) -> tuple[str, str | None]:
        if token.isdigit():
            return token, None

        if self._contains_cyrillic(token) and not self._contains_latin(token):
            lemma = self._morph.parse(token)[0].normal_form
        elif self._contains_latin(token) and not self._contains_cyrillic(token):
            lemma = lemmatize(token, lang="en")
        else:
            return token, None

        if lemma != token:
            return lemma, f"lemma:{token}->{lemma}"

        return token, None

    def _score_russian_token(self, token: str) -> float:
        if not self._contains_cyrillic(token) or self._contains_latin(token):
            return 0.0

        score = in_target_language(token, "ru")

        if self._morph.word_is_known(token):
            score += 1.0

        if token in RUSSIAN_STOP_WORDS:
            score += 0.25

        return score

    def _score_english_token(self, token: str) -> float:
        if not self._contains_latin(token) or self._contains_cyrillic(token):
            return 0.0

        score = in_target_language(token, "en")

        if is_known(token, lang="en"):
            score += 1.0

        if token in ENGLISH_STOP_WORDS:
            score += 0.25

        return score

    def _dominant_script_alias(self, token: str) -> str | None:
        counts = {"LATIN": 0, "CYRILLIC": 0}

        for char in token:
            alias = self._script_alias(char)
            if alias in counts:
                counts[alias] += 1

        if counts["LATIN"] == counts["CYRILLIC"] == 0:
            return None

        return "CYRILLIC" if counts["CYRILLIC"] >= counts["LATIN"] else "LATIN"

    def _split_by_script(self, token: str) -> list[str]:
        pieces: list[str] = []
        current: list[str] = []
        current_alias: str | None = None

        for char in token:
            alias = self._script_alias(char)

            if alias == "COMMON":
                current.append(char)
                continue

            if current_alias is None or alias == current_alias:
                current.append(char)
                current_alias = alias
                continue

            pieces.append("".join(current))
            current = [char]
            current_alias = alias

        if current:
            pieces.append("".join(current))

        return [piece for piece in pieces if piece]

    def _script_alias(self, char: str) -> str:
        alias = confusables.alias(char)
        return alias if alias in SCRIPT_ALIASES else "COMMON"

    def _contains_latin(self, token: str) -> bool:
        return bool(LATIN_RE.search(token))

    def _contains_cyrillic(self, token: str) -> bool:
        return bool(CYRILLIC_RE.search(token))

    def _render_normalized_query(self, tokens: list[str]) -> str:
        rendered_parts: list[str] = []

        for token in tokens:
            if token in PUNCTUATION_TOKENS and rendered_parts:
                rendered_parts[-1] = f"{rendered_parts[-1]}{token}"
                continue

            rendered_parts.append(token)

        return " ".join(rendered_parts)

import re

import jellyfish
from markdown import Markdown
from markdown_plain_text.extention import PlainTextExtension


def normalize_key(text):
    """Normalize entry titles and user queries for lookup/search keys."""
    text = text.lower()
    text = re.sub(r"[^\w\s'-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text, flags=re.UNICODE)
    return text


def phonetic_code(text):
    """Return a metaphone code used to find plausible misspellings."""
    text = normalize_key(text)
    text = re.sub(r"[^a-zA-Z]", "", text, flags=re.UNICODE)
    return jellyfish.metaphone(text)


def markdown_to_plain_text(text):
    """Convert entry Markdown to plain text for indexing and plain output."""
    md = Markdown(extensions=[PlainTextExtension()])
    return md.convert(text)


def extract_first_heading(markdown):
    match = re.search(r"^#\s+(.+?)\s*$", markdown, flags=re.MULTILINE)
    return match.group(1) if match else None


def extract_forwarding_target(body, headword):
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if len(lines) != 2:
        return None

    plain_headword = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>])", r"\1", headword)
    pattern = rf"^(?:{re.escape(plain_headword)}\.\s+)?See (.+)\.\Z"
    match = re.search(pattern, lines[1])
    if match:
        return match.group(1).strip()
    else:
        return None


def is_essay_heading(title):
    return title.endswith(", Essay")


def parse_headword(headword):
    """Remove display-only essay suffixes while preserving essay metadata."""
    is_essay = is_essay_heading(headword)
    if is_essay:
        headword = headword.removesuffix(", Essay")
    return headword, is_essay


def parse_lookup_query(word):
    """Return the normalized lookup key and whether the user asked for an essay."""
    key = normalize_key(word).strip()
    if key.endswith(" essay"):
        return key.removesuffix(" essay").strip(), True
    return key, None


def split_search_words(text):
    return [word for word in re.split(r"[\s'-]+", text) if word]

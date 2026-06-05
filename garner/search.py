import jellyfish

from garner.text import phonetic_code, split_search_words


SEARCH_EXACT = 0
SEARCH_PREFIX = 1
SEARCH_WORD_PREFIX = 2
SEARCH_SUBSTRING = 3
SEARCH_PHONETIC = 4
SEARCH_FUZZY = 5
SEARCH_MAX_FUZZY_RATIO = 0.45
SEARCH_MIN_FUZZY_SIMILARITY = 0.86


def search_score(word, row):
    """Return a sortable score for ranked dictionary search results."""
    sort_key = row["sort_key"]
    row_phonetic_code = row["phonetic_code"]
    query_phonetic_code = phonetic_code(word)

    if sort_key == word:
        bucket = SEARCH_EXACT
    elif sort_key.startswith(word):
        bucket = SEARCH_PREFIX
    elif any(part.startswith(word) for part in split_search_words(sort_key)):
        bucket = SEARCH_WORD_PREFIX
    elif word in sort_key:
        bucket = SEARCH_SUBSTRING
    elif len(query_phonetic_code) >= 2 and (row_phonetic_code == query_phonetic_code or row_phonetic_code.startswith(query_phonetic_code)):
        bucket = SEARCH_PHONETIC
    else:
        bucket = SEARCH_FUZZY

    distance = jellyfish.levenshtein_distance(word, sort_key)
    similarity = jellyfish.jaro_winkler_similarity(word, sort_key)
    return (bucket, distance, -similarity, row["is_essay"], sort_key)


def is_search_match(score, word):
    bucket, distance, negative_similarity, _, _ = score
    if bucket < SEARCH_FUZZY:
        return True

    return (
        distance / max(len(word), 1) <= SEARCH_MAX_FUZZY_RATIO
        and -negative_similarity >= SEARCH_MIN_FUZZY_SIMILARITY
    )

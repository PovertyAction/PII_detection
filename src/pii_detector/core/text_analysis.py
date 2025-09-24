"""Text analysis for finding PII in unstructured text data."""

import re
from pathlib import Path

from pii_detector.api.queries import find_names_in_list_string
from pii_detector.data import restricted_words as restricted_words_list
from pii_detector.data.constants import ENGLISH, SPANISH


def get_stopwords(languages: list[str] | None = None) -> list[str]:
    """Load stopwords from data directory.

    Args:
        languages: List of language names to load, or None for all languages

    Returns:
        List of stopwords

    """
    # Get path to stopwords directory in the package
    stopwords_path = Path(__file__).parent.parent / "data" / "stopwords"

    # If no language selected, get all stopwords
    if languages is None:
        stopwords_files = [f for f in stopwords_path.iterdir() if f.is_file()]
    else:
        # Select only stopwords files for given languages
        stopwords_files = []
        for language in languages:
            file_path = stopwords_path / language
            if file_path.is_file():
                stopwords_files.append(file_path)

    stopwords_list = []
    for file_path in stopwords_files:
        try:
            with open(file_path, encoding="utf-8") as reader:
                stopwords = reader.read().split("\n")
                stopwords_list.extend(stopwords)
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, encoding="latin-1") as reader:
                stopwords = reader.read().split("\n")
                stopwords_list.extend(stopwords)

    return list(set(stopwords_list))


def remove_stopwords(
    strings_list: list[str], languages: list[str] = ["english", "spanish"]
) -> list[str]:
    """Remove stopwords from a list of strings.

    Args:
        strings_list: List of strings to filter
        languages: Languages to use for stopword filtering

    Returns:
        Filtered list of strings

    """
    stop_words = get_stopwords(languages)
    return [s for s in strings_list if s not in stop_words]


def find_phone_numbers_in_list_strings(list_strings: list[str]) -> list[str]:
    """Find phone numbers in a list of strings using regex patterns.

    Args:
        list_strings: List of strings to search

    Returns:
        List of strings that match phone number patterns

    """
    phone_n_regex_str = r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})"
    phone_n_regex = re.compile(phone_n_regex_str)
    phone_numbers_found = [s for s in list_strings if phone_n_regex.match(s)]

    return phone_numbers_found


def filter_based_type_of_word(list_strings: list[str], language: str) -> list[str]:
    """Filter strings based on word type analysis.

    Args:
        list_strings: List of strings to analyze
        language: Language for analysis context

    Returns:
        Filtered list of strings

    """
    # This is a placeholder for more sophisticated NLP analysis
    # In the original, this used spacy for linguistic analysis
    # For now, we'll do basic filtering

    # Remove single characters and very short strings
    filtered = [s for s in list_strings if len(s) > 2]

    # Remove strings that are mostly numbers
    filtered = [
        s
        for s in filtered
        if not s.replace(" ", "").replace("-", "").replace(".", "").isdigit()
    ]

    return filtered


def extract_words_from_text(text: str, language: str = ENGLISH) -> list[str]:
    """Extract individual words from text for PII analysis.

    Args:
        text: Text to analyze
        language: Language context for processing

    Returns:
        List of extracted words

    """
    # Basic word extraction - split on common delimiters
    words = re.split(r"[\s,;.!?\-_]+", text)

    # Clean up words
    words = [word.strip() for word in words if word.strip()]

    # Remove stopwords
    language_map = {ENGLISH: "english", SPANISH: "spanish"}
    lang_code = language_map.get(language, "english")
    words = remove_stopwords(words, [lang_code])

    return words


def find_potential_names_in_text(text: str, language: str = ENGLISH) -> list[str]:
    """Find potential person names in text.

    Args:
        text: Text to analyze
        language: Language context

    Returns:
        List of potential names found

    """
    words = extract_words_from_text(text, language)

    # Filter by word type
    potential_names = filter_based_type_of_word(words, language)

    # Use external API to validate names (if available)
    try:
        validated_names = find_names_in_list_string(potential_names)
        return validated_names
    except Exception as e:
        print(f"Could not validate names via API: {e}")
        # Fall back to basic heuristics
        return [name for name in potential_names if name.istitle()]


def find_locations_in_text(text: str) -> list[str]:
    """Find potential location names in text.

    Args:
        text: Text to analyze

    Returns:
        List of potential locations found

    """
    words = extract_words_from_text(text)

    # Get location-related restricted words
    location_words = (
        restricted_words_list.get_locations_strict_restricted_words()
        + restricted_words_list.get_locations_fuzzy_restricted_words()
    )

    # Find words that match location patterns
    potential_locations = []
    for word in words:
        for location_word in location_words:
            if (
                location_word.lower() in word.lower()
                or word.lower() in location_word.lower()
            ):
                potential_locations.append(word)

    return list(set(potential_locations))


def replace_piis_in_text(
    text: str, replacement: str = "XXXXXX", language: str = ENGLISH
) -> str:
    """Replace detected PIIs in text with a placeholder.

    Args:
        text: Original text
        replacement: String to replace PIIs with
        language: Language context for processing

    Returns:
        Text with PIIs replaced

    """
    modified_text = text

    # Find and replace names
    names = find_potential_names_in_text(text, language)
    for name in names:
        modified_text = re.sub(
            rf"\b{re.escape(name)}\b", replacement, modified_text, flags=re.IGNORECASE
        )

    # Find and replace phone numbers
    phone_numbers = find_phone_numbers_in_list_strings([text])
    for phone in phone_numbers:
        modified_text = modified_text.replace(phone, replacement)

    # Find and replace locations (if they seem to be small/specific)
    locations = find_locations_in_text(text)
    for location in locations:
        modified_text = re.sub(
            rf"\b{re.escape(location)}\b",
            replacement,
            modified_text,
            flags=re.IGNORECASE,
        )

    return modified_text


def find_piis_in_unstructured_text(text_series, language: str = ENGLISH) -> set[str]:
    """Find PIIs in unstructured text data.

    Args:
        text_series: Pandas series or list of text strings
        language: Language context for processing

    Returns:
        Set of detected PIIs

    """
    all_piis = set()

    # Convert to list if it's a pandas series
    if hasattr(text_series, "tolist"):
        texts = text_series.tolist()
    else:
        texts = list(text_series)

    for text in texts:
        if not isinstance(text, str):
            continue

        # Find different types of PIIs
        names = find_potential_names_in_text(text, language)
        locations = find_locations_in_text(text)
        phone_numbers = find_phone_numbers_in_list_strings([text])

        all_piis.update(names)
        all_piis.update(locations)
        all_piis.update(phone_numbers)

    return all_piis

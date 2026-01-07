"""Data, constants, and configuration for PII detection."""

from pii_detector.data.constants import (
    CHECK_LOCATIONS_POP,
    COLUMNS_FORMAT_SEARCH_METHOD,
    COLUMNS_NAMES_SEARCH_METHOD,
    CONSIDER_SURVEY_CTO_VARS,
    DATASET,
    DATE,
    ENGLISH,
    ERROR_MESSAGE,
    FUZZY,
    LOCATIONS_POPULATIONS_SEARCH_METHOD,
    OTHER,
    PHONE_NUMBER,
    PII_CANDIDATES,
    SPANISH,
    SPARSE_ENTRIES_SEARCH_METHOD,
    STRICT,
    UNSTRUCTURED_TEXT_SEARCH_METHOD,
)
from pii_detector.data.restricted_words import (
    get_fuzzy_restricted_words,
    get_locations_fuzzy_restricted_words,
    get_locations_strict_restricted_words,
    get_strict_restricted_words,
    get_surveycto_restricted_vars,
)

__all__ = [
    # Constants
    "CHECK_LOCATIONS_POP",
    "COLUMNS_FORMAT_SEARCH_METHOD",
    "COLUMNS_NAMES_SEARCH_METHOD",
    "CONSIDER_SURVEY_CTO_VARS",
    "DATASET",
    "DATE",
    "ENGLISH",
    "ERROR_MESSAGE",
    "FUZZY",
    "LOCATIONS_POPULATIONS_SEARCH_METHOD",
    "OTHER",
    "PHONE_NUMBER",
    "PII_CANDIDATES",
    "SPARSE_ENTRIES_SEARCH_METHOD",
    "SPANISH",
    "STRICT",
    "UNSTRUCTURED_TEXT_SEARCH_METHOD",
    # Functions
    "get_fuzzy_restricted_words",
    "get_locations_fuzzy_restricted_words",
    "get_locations_strict_restricted_words",
    "get_strict_restricted_words",
    "get_surveycto_restricted_vars",
]

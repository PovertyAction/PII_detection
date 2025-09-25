"""Core PII detection and data processing functionality."""

import warnings

import pandas as pd

from pii_detector.api.queries import query_location_population
from pii_detector.data import constants
from pii_detector.data import restricted_words as restricted_words_list

warnings.simplefilter(action="ignore", category=FutureWarning)

# Global variables for output management
OUTPUTS_FOLDER = None
LOG_FILE_PATH = None


def get_surveycto_restricted_vars() -> list[str]:
    """Get SurveyCTO restricted variables."""
    return restricted_words_list.get_surveycto_restricted_vars()


def import_dataset(dataset_path: str) -> tuple[bool, str | list]:
    """Import a dataset from various file formats.

    Args:
        dataset_path: Path to the dataset file

    Returns:
        Tuple of (success, result) where result is either error message or
        [dataset, dataset_path, label_dict, value_label_dict]

    """
    dataset, label_dict, value_label_dict = False, False, False
    status_message = False

    # Check format
    if not dataset_path.endswith(("xlsx", "xls", "csv", "dta")):
        return (False, "Supported files are .csv, .dta, .xlsx, .xls")

    try:
        if dataset_path.endswith(("xlsx", "xls")):
            dataset = pd.read_excel(dataset_path)
        elif dataset_path.endswith("csv"):
            dataset = pd.read_csv(dataset_path)
        elif dataset_path.endswith("dta"):
            try:
                dataset = pd.read_stata(dataset_path)
            except ValueError:
                dataset = pd.read_stata(dataset_path, convert_categoricals=False)
            label_dict = pd.io.stata.StataReader(dataset_path).variable_labels()
            try:
                value_label_dict = pd.io.stata.StataReader(dataset_path).value_labels()
            except AttributeError:
                status_message = "No value labels detected."
        elif dataset_path.endswith(("xpt", ".sas7bdat")):
            dataset = pd.read_sas(dataset_path)
        elif dataset_path.endswith("vc"):
            status_message = (
                "**ERROR**: This folder appears to be encrypted using VeraCrypt."
            )
            raise Exception
        elif dataset_path.endswith("bc"):
            status_message = "**ERROR**: This file appears to be encrypted using Boxcryptor. Sign in to Boxcryptor and then select the file in your X: drive."
            raise Exception
        else:
            raise Exception

    except (FileNotFoundError, Exception):
        if status_message is False:
            status_message = "**ERROR**: This path appears to be invalid. If your folders or filename contain colons or commas, try renaming them or moving the file to a different location."
        raise

    if status_message:
        log_and_print("There was an error")
        log_and_print(status_message)
        return (False, status_message)

    log_and_print("The dataset has been read successfully.\n")
    dataset_read_return = [dataset, dataset_path, label_dict, value_label_dict]
    return (True, dataset_read_return)


def word_match(
    column_name: str, restricted_word: str, type_of_matching: str = constants.STRICT
) -> bool:
    """Check if a column name matches a restricted word."""
    if type_of_matching == constants.STRICT:
        return column_name.lower() == restricted_word.lower()
    else:  # type_of_matching == FUZZY
        return restricted_word.lower() in column_name.lower()


def remove_other_refuse_and_dont_know(column: pd.Series) -> pd.Series:
    """Remove standard survey response values like 999, -999, etc."""
    # List of values to remove. All numbers with 3 digits where all digits are the same
    values_to_remove = [str(111 * i) for i in range(-9, 10) if i != 0]
    filtered_column = column[~column.isin(values_to_remove)]
    return filtered_column


def clean_column(column: pd.Series) -> pd.Series:
    """Clean a column by removing NaNs, empty entries, and standard survey codes."""
    # Drop NaNs
    column_filtered = column.dropna()

    # Remove empty entries
    column_filtered = column_filtered[column_filtered != ""]

    # Remove other, refuses and don't knows
    if len(column_filtered) != 0:
        column_filtered = remove_other_refuse_and_dont_know(column_filtered)

    return column_filtered


def column_is_sparse(
    dataset: pd.DataFrame, column_name: str, sparse_threshold: float
) -> bool:
    """Check if a column is sparse (has high ratio of unique values)."""
    column_filtered = clean_column(dataset[column_name])

    # Check sparsity
    n_entries = len(column_filtered)
    n_unique_entries = column_filtered.nunique()

    return n_entries != 0 and n_unique_entries / n_entries > sparse_threshold


def column_has_sufficiently_sparse_strings(
    dataset: pd.DataFrame, column_name: str, sparse_threshold: float = 0.2
) -> bool:
    """Check if 'valid' column entries are sparse.

    Only considers string columns and excludes NaN, empty, and survey codes.
    """
    # Check if column type is string
    if dataset[column_name].dtypes == "object":
        return column_is_sparse(dataset, column_name, sparse_threshold)
    else:
        return False


def column_has_sparse_value_label_dicts(
    column_name: str, value_label_dict: dict, sparse_threshold: int = 10
) -> bool:
    """Check if a column has sufficiently sparse value label dictionary."""
    return (
        column_name in value_label_dict
        and value_label_dict[column_name] != ""
        and len(value_label_dict[column_name]) > sparse_threshold
    )


def log_and_print(message: str) -> None:
    """Log a message to file and print to console."""
    print(message)
    if LOG_FILE_PATH:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")


def find_piis_based_on_column_name(
    dataset: pd.DataFrame,
    label_dict: dict,
    language: str,
    country: str,
    matching_type: str = constants.STRICT,
) -> list[str]:
    """Find PIIs based on column name/label matching against restricted word lists.

    Args:
        dataset: The pandas DataFrame to analyze
        label_dict: Dictionary mapping column names to their labels
        language: Language for word matching
        country: Country for location-specific matching
        matching_type: Type of matching (strict or fuzzy)

    Returns:
        List of column names identified as potential PII

    """
    pii_columns = []

    for column_name in dataset.columns:
        # Get column label if available
        column_label = (
            label_dict.get(column_name, column_name) if label_dict else column_name
        )

        # Check against various restricted word lists
        if _matches_restricted_words(
            column_name, column_label, language, country, matching_type
        ):
            pii_columns.append(column_name)
            log_and_print(f"PII detected (column name): {column_name}")

    return pii_columns


def find_piis_based_on_column_format(dataset: pd.DataFrame) -> list[str]:
    """Find PIIs based on column format patterns (phone numbers, dates, etc.).

    Args:
        dataset: The pandas DataFrame to analyze

    Returns:
        List of column names identified as potential PII based on format

    """
    pii_columns = []

    for column_name in dataset.columns:
        column_data = clean_column(dataset[column_name])

        if _contains_phone_numbers(column_data):
            pii_columns.append(column_name)
            log_and_print(f"PII detected (phone format): {column_name}")
        elif _contains_date_patterns(column_data):
            pii_columns.append(column_name)
            log_and_print(f"PII detected (date format): {column_name}")
        elif _contains_email_patterns(column_data):
            pii_columns.append(column_name)
            log_and_print(f"PII detected (email format): {column_name}")

    return pii_columns


def find_piis_based_on_sparse_entries(
    dataset: pd.DataFrame, sparse_threshold: float = 0.8
) -> list[str]:
    """Find PIIs based on sparsity analysis (columns with mostly unique values).

    Args:
        dataset: The pandas DataFrame to analyze
        sparse_threshold: Minimum sparsity ratio to flag as PII

    Returns:
        List of column names identified as potential PII based on sparsity

    """
    pii_columns = []

    for column_name in dataset.columns:
        if column_is_sparse(dataset, column_name, sparse_threshold):
            pii_columns.append(column_name)
            log_and_print(f"PII detected (sparse): {column_name}")
        elif column_has_sufficiently_sparse_strings(
            dataset, column_name, sparse_threshold
        ):
            pii_columns.append(column_name)
            log_and_print(f"PII detected (sparse strings): {column_name}")

    return pii_columns


def find_piis_based_on_locations_population(
    dataset: pd.DataFrame, population_threshold: int = 20000, country: str = "US"
) -> list[str]:
    """Find PIIs based on location population analysis (small locations may be PII).

    Args:
        dataset: The pandas DataFrame to analyze
        population_threshold: Maximum population size to consider as PII
        country: Country code for location lookups (default: 'US')

    Returns:
        List of column names identified as potential PII based on location population

    """
    pii_columns = []

    for column_name in dataset.columns:
        if _contains_small_locations(
            dataset[column_name], population_threshold, country
        ):
            pii_columns.append(column_name)
            log_and_print(f"PII detected (small location): {column_name}")

    return pii_columns


def _matches_restricted_words(
    column_name: str, column_label: str, language: str, country: str, matching_type: str
) -> bool:
    """Check if column name/label matches any restricted words."""
    # Get appropriate restricted word lists
    if matching_type == constants.STRICT:
        word_lists = [
            restricted_words_list.get_strict_restricted_words(),
            restricted_words_list.get_locations_strict_restricted_words(),
            restricted_words_list.get_surveycto_restricted_vars(),
        ]
    else:  # FUZZY matching
        word_lists = [
            restricted_words_list.get_fuzzy_restricted_words(),
            restricted_words_list.get_locations_fuzzy_restricted_words(),
        ]

    for word_list in word_lists:
        for restricted_word in word_list:
            if word_match(column_name, restricted_word, matching_type):
                return True
            if column_label != column_name and word_match(
                column_label, restricted_word, matching_type
            ):
                return True

    return False


def _contains_phone_numbers(column_data: pd.Series) -> bool:
    """Check if column contains phone number patterns."""
    import re

    phone_pattern = re.compile(r"[\+]?[\d\s\-\(\)]{10,}")

    sample_size = min(100, len(column_data))
    sample_data = column_data.dropna().head(sample_size)

    phone_count = 0
    for value in sample_data:
        if isinstance(value, str) and phone_pattern.search(value):
            phone_count += 1

    return phone_count / len(sample_data) > 0.5 if len(sample_data) > 0 else False


def _contains_date_patterns(column_data: pd.Series) -> bool:
    """Check if column contains date patterns."""
    import re

    date_patterns = [
        re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"),  # MM/DD/YYYY or DD/MM/YYYY
        re.compile(r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"),  # YYYY/MM/DD
        re.compile(
            r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4}",
            re.IGNORECASE,
        ),
    ]

    sample_size = min(100, len(column_data))
    sample_data = column_data.dropna().head(sample_size)

    date_count = 0
    for value in sample_data:
        if isinstance(value, str):
            for pattern in date_patterns:
                if pattern.search(value):
                    date_count += 1
                    break

    return date_count / len(sample_data) > 0.5 if len(sample_data) > 0 else False


def _contains_email_patterns(column_data: pd.Series) -> bool:
    """Check if column contains email patterns."""
    import re

    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    sample_size = min(100, len(column_data))
    sample_data = column_data.dropna().head(sample_size)

    email_count = 0
    for value in sample_data:
        if isinstance(value, str) and email_pattern.search(value):
            email_count += 1

    return email_count / len(sample_data) > 0.5 if len(sample_data) > 0 else False


def _contains_small_locations(
    column_data: pd.Series, population_threshold: int, country: str = "US"
) -> bool:
    """Check if column contains locations with small populations."""
    sample_size = min(50, len(column_data))  # Limit API calls
    sample_data = column_data.dropna().unique()[:sample_size]

    small_location_count = 0
    for location in sample_data:
        if isinstance(location, str) and len(location.strip()) > 2:
            try:
                population = query_location_population(location.strip(), country)
                if population and population < population_threshold:
                    small_location_count += 1
            except Exception as e:
                log_and_print(f"Error querying location {location}: {e}")
                continue

    return (
        small_location_count / len(sample_data) > 0.3 if len(sample_data) > 0 else False
    )

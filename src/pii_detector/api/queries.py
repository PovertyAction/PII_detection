"""External API integrations for location population lookups and other queries."""

import json
import os

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from pii_detector.data.constants import COUNTRY_NAME_TO_ISO_CODE

# Global driver instance for Google queries
_driver = None


def get_api_credentials() -> dict[str, str | None]:
    """Get API credentials from environment variables."""
    return {
        "geonames_username": os.environ.get("GEONAMES_USERNAME"),
        "forebears_api_key": os.environ.get("FOREBEARS_API_KEY"),
    }


def ask_google(query: str) -> str | bool:
    """Query Google for population information."""
    global _driver

    if _driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1024x768")
        chrome_options.add_argument("--headless")
        try:
            _driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Could not initialize Chrome driver: {e}")
            return False

    try:
        # Search for query
        query = query.replace(" ", "+")
        _driver.get("http://www.google.com/search?q=" + query)

        # Get text from Google answer box
        for y_location in [230, 350]:
            answer = _driver.execute_script(
                "return document.elementFromPoint(arguments[0], arguments[1]);",
                350,
                y_location,
            ).text
            if answer != "":
                return answer

        return False
    except Exception as e:
        print(f"Error querying Google: {e}")
        return False


def get_country_iso_code(country_name: str) -> str | None:
    """Get ISO country code from country name."""
    return COUNTRY_NAME_TO_ISO_CODE.get(country_name)


def check_location_exists_and_population_size(
    location: str, country: str
) -> tuple[bool, int | bool]:
    """Check if a location exists and get its population using GeoNames API.

    Returns:
        Tuple of (location_exists, population)
        population can be int, False (if unknown), or bool False if location doesn't exist

    """
    credentials = get_api_credentials()
    username = credentials.get("geonames_username")

    if not username:
        print("Warning: GEONAMES_USERNAME not set in environment variables")
        return False, False

    api_url = (
        f"http://api.geonames.org/searchJSON?name={location}&name_equals={location}"
        f"&maxRows=1&orderby=population&isNameRequired=true&username={username}"
    )

    country_iso = get_country_iso_code(country)
    if country_iso:
        api_url += f"&country={country_iso}"

    try:
        response = requests.get(api_url, timeout=10)
        response_json = response.json()

        if (
            "totalResultsCount" in response_json
            and response_json["totalResultsCount"] > 0
        ):
            geoname = response_json["geonames"][0]
            if "population" in geoname and geoname["population"] != 0:
                return True, geoname["population"]
            else:
                return True, False
        else:
            return False, False

    except Exception as e:
        print(f"Error querying GeoNames API: {e}")
        return False, False


def get_population_from_google_query_result(query_result: str) -> int | bool:
    r"""Parse population from Google query result.

    Handles formats like:
    - 3,685\n2010
    - 91,411 (2018)
    - 14,810,001
    - 17 million people
    - 1.655 million (2010)
    """
    try:
        clean_query_result = query_result

        # Remove commas: 14,810,001
        clean_query_result = clean_query_result.replace(",", "")

        # Handle newlines: 3685\\n2010
        clean_query_result = clean_query_result.split("\\n")[0]

        # Handle parentheses and extra text
        if " " in clean_query_result:
            parts = clean_query_result.split(" ")
            # Keep only the number and potential multiplier
            if len(parts) > 1 and parts[1] in ["million", "thousand"]:
                clean_query_result = f"{parts[0]} {parts[1]}"
            else:
                clean_query_result = parts[0]

        # Handle millions: 1.655 million
        if " " in clean_query_result:
            number_str, multiplier = clean_query_result.split(" ")
            result = float(number_str)
            if multiplier == "million":
                result = result * 1000000
            elif multiplier == "thousand":
                result = result * 1000
            clean_query_result = str(int(result))

        return int(clean_query_result)

    except Exception as e:
        print(f"Error parsing population from Google result: {e}")
        return False


def google_population(location: str) -> int | bool:
    """Get population of a location by querying Google."""
    query_result = ask_google(f"{location} population")

    if query_result:
        population = get_population_from_google_query_result(query_result)
        return population
    else:
        return False


def get_locations_with_low_population(
    locations: list[str],
    country: str,
    low_population_threshold: int = 20000,
    return_one: bool | None = None,
    consider_low_population_if_unknown_population: bool = False,
) -> list[str] | str | bool:
    """Check which locations have low population.

    Args:
        locations: List of location names to check
        country: Country name for context
        low_population_threshold: Population threshold for "low population"
        return_one: If True, return first location with low population
        consider_low_population_if_unknown_population: If True, treat unknown as low

    Returns:
        List of locations with low population, or single location if return_one=True,
        or False if none found when return_one=True

    """
    locations_with_low_population = []
    locations_with_unknown_population = []

    for index, location in enumerate(locations):
        if index % 50 == 0:
            print(f"{index}/{len(locations)}: {location}")

        location_exists, population = check_location_exists_and_population_size(
            location, country
        )

        if location_exists:
            if not population:
                population = google_population(location)

            if population:
                print(f"Found population for {location}: {population}")
                if population < low_population_threshold:
                    print(f"{location} has LOW population")
                    if return_one:
                        return location
                    else:
                        locations_with_low_population.append(location)
                else:
                    # Found a location with known population - now consider unknowns as low
                    if not consider_low_population_if_unknown_population:
                        locations_with_low_population.extend(
                            locations_with_unknown_population
                        )
                        consider_low_population_if_unknown_population = True
            else:
                # Unknown population
                if consider_low_population_if_unknown_population:
                    if return_one:
                        return location
                    else:
                        locations_with_low_population.append(location)
                else:
                    locations_with_unknown_population.append(location)

    if return_one:
        return False
    else:
        return locations_with_low_population


def find_names_in_list_string(list_potential_names: list[str]) -> list[str]:
    """Find actual names from a list of potential names using Forebears API.

    Note: Requires FOREBEARS_API_KEY environment variable.
    """
    credentials = get_api_credentials()
    api_key = credentials.get("forebears_api_key")

    if not api_key:
        print("Warning: FOREBEARS_API_KEY not set in environment variables")
        return []

    all_names_found = set()

    # API calls must query at most 1,000 names
    n = 1000
    chunks = [
        list_potential_names[i : i + n] for i in range(0, len(list_potential_names), n)
    ]

    for chunk in chunks:
        for name_type in ["forename", "surname"]:
            try:
                api_url = f"https://ono.4b.rs/v1/jurs?key={api_key}"
                names_parameter = _generate_names_parameter_for_api(chunk, name_type)

                response = requests.post(
                    api_url, data={"names": names_parameter}, timeout=30
                )

                names_found = _get_names_from_json_response(response.text)
                all_names_found.update(names_found)

            except Exception as e:
                print(f"Error querying Forebears API: {e}")

    return list(all_names_found)


def _generate_names_parameter_for_api(list_names: list[str], option: str) -> str:
    """Generate names parameter for Forebears API."""
    list_of_names_json = []
    for name in list_names:
        list_of_names_json.append(f'{{"name":"{name}","type":"{option}","limit":2}}')

    return "[" + ",".join(list_of_names_json) + "]"


def _get_names_from_json_response(response: str) -> list[str]:
    """Extract names from Forebears API JSON response."""
    names_found = []

    try:
        json_response = json.loads(response)

        if "results" in json_response:
            for result in json_response["results"]:
                # Names that exist come with the field 'jurisdictions'
                # We will also ask a minimum of 50 world incidences
                if "jurisdictions" in result and len(result["jurisdictions"]) > 0:
                    try:
                        world_incidences = int(result["world"]["incidence"])
                        if world_incidences > 50:
                            names_found.append(result["name"])
                    except Exception as e:
                        print(f"Error processing result: {e}")
        else:
            print("No results in response")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")

    return names_found


def cleanup_driver():
    """Clean up the global webdriver instance."""
    global _driver
    if _driver:
        try:
            _driver.quit()
            _driver = None
        except Exception as e:
            print(f"Error closing driver: {e}")


def query_location_population(location: str, country: str) -> int | None:
    """Query location population from external APIs.

    Args:
        location: Location name
        country: Country name

    Returns:
        Population number or None if not found

    """
    location_exists, population = check_location_exists_and_population_size(
        location, country
    )

    if location_exists and population:
        return population
    elif location_exists:
        # Try Google as backup
        google_pop = google_population(location)
        return google_pop if google_pop else None
    else:
        return None

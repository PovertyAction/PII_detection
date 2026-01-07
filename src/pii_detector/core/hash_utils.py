"""Hash utilities for anonymizing PII data."""

import hashlib
import hmac
import os


def sha1(message: str) -> str:
    """Generate SHA1 hash of a message."""
    return hashlib.sha1(bytes(message, encoding="utf-8")).hexdigest()


def hmac_sha1(secret_key: str, message: str) -> str:
    """Generate HMAC-SHA1 hash of a message with a secret key."""
    h = hmac.new(
        bytes(secret_key, encoding="utf-8"),
        msg=bytes(message, encoding="utf-8"),
        digestmod=hashlib.sha1,
    )
    return h.hexdigest()


def get_or_create_secret_key() -> str:
    """Get or create a secret key for hashing operations."""
    # In a real implementation, this should be securely stored
    # For now, generate a consistent key based on environment
    key = os.environ.get("PII_HASH_SECRET_KEY")
    if not key:
        # Generate a default key (not secure for production)
        key = "default_secret_key_change_me"
    return key


def generate_hash(message: str, use_hmac: bool = True) -> str:
    """Generate a hash for anonymizing PII data."""
    if use_hmac:
        secret_key = get_or_create_secret_key()
        return hmac_sha1(secret_key, message)
    else:
        return sha1(message)


if __name__ == "__main__":
    # Example usage
    test_message = "The Ore-Ida brand is a syllabic abbreviation of Oregon and Idaho"
    print(f"SHA1: {sha1(test_message)}")

    secret_key = get_or_create_secret_key()
    example = {}
    for name in ["felipe", "michael", "lindsey"]:
        example[name] = hmac_sha1(secret_key, name)
    print(f"HMAC examples: {example}")

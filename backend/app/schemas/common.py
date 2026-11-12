"""Shared, hardened field types for the request schemas.

Everything here exists to make the API reject, with a clean 422, input that
the database would otherwise reject with an unhandled error (a 500) or, worse,
silently alter.
"""

from typing import Annotated

from pydantic import AfterValidator, StringConstraints

# Largest value that fits in a PostgreSQL INTEGER (int4) column. Ids and
# counters above this make PostgreSQL raise "integer out of range".
INT4_MAX = 2_147_483_647


def _reject_nul(value: str) -> str:
    # PostgreSQL text columns cannot store NUL (0x00); psycopg raises a
    # DataError for it, which would surface as an HTTP 500.
    if "\x00" in value:
        raise ValueError("NUL (0x00) characters are not allowed")
    return value


def _text(max_length: int, *, min_length: int = 1):
    return Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=min_length,
            max_length=max_length,
        ),
        AfterValidator(_reject_nul),
    ]


# Lengths mirror (or are stricter than) the database columns.
PersonName = _text(150)
ProductName = _text(100)  # DB column allows 150
Brand = _text(50)         # DB column is VARCHAR(50)
CategoryName = _text(100)
Description = _text(500, min_length=0)

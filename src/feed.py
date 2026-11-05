"""Helpers for the sec-gov/filings/daily_index_changes response."""


def tracked_filings(records: list, tracked: dict) -> list:
    """Return the feed records whose CIK belongs to a tracked company (CIK to ticker map)."""
    return [r for r in records if r["cik"] in tracked]

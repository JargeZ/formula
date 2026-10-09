"""Random helpers for seed data. One seeded generator keeps every run identical."""

import random
from datetime import timedelta

from django.utils import timezone

rng = random.Random(2026)


def past(days, min_days=0):
    """Random aware datetime between `days` and `min_days` days ago."""
    seconds = rng.randint(min_days * 86400, days * 86400)
    return timezone.now() - timedelta(seconds=seconds)


def weighted(choices):
    """Pick a key from a {value: weight} dict."""
    return rng.choices(list(choices), weights=list(choices.values()))[0]


def paragraphs(*texts):
    # Trix (Unfold WYSIWYG) keeps blocks as <div>, <p> would be merged into one line
    return "".join(f"<div>{text}</div>" for text in texts)

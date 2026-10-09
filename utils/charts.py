"""Helpers that build data for Unfold chart, progress and KPI components."""

import json

PALETTE = [
    "var(--color-primary-700)",
    "var(--color-primary-500)",
    "var(--color-primary-300)",
    "var(--color-primary-200)",
    "var(--color-base-400)",
    "var(--color-base-300)",
    "var(--color-base-200)",
]


def chart(labels, *datasets):
    """JSON for `data-value` of an Unfold chart: datasets are (label, values) pairs."""
    return json.dumps(
        {
            "labels": [str(label) for label in labels],
            "datasets": [
                {
                    "label": str(label),
                    "data": [float(value or 0) for value in values],
                    "backgroundColor": PALETTE[index % len(PALETTE)],
                    "borderColor": PALETTE[index % len(PALETTE)],
                }
                for index, (label, values) in enumerate(datasets)
            ],
        }
    )


def pie(labels, values):
    """JSON for pie / doughnut / radar charts: one dataset with a color per slice."""
    return json.dumps(
        {
            "labels": [str(label) for label in labels],
            "datasets": [
                {
                    "data": [float(value or 0) for value in values],
                    "backgroundColor": [
                        PALETTE[i % len(PALETTE)] for i in range(len(values))
                    ],
                }
            ],
        }
    )


def percent(part, total):
    return round(part * 100 / total, 1) if total else 0


def kpi(title, total, current, previous):
    """Context for `formula/helpers/kpi_progress.html`: value with a trend arrow."""
    change = percent(current - previous, previous)
    return {
        "title": title,
        "total": total,
        "percentage": f"{change:+}%",
        "progress": "positive" if change >= 0 else "negative",
    }

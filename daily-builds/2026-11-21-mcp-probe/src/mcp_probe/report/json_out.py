"""JSON formatter."""

import json
from ..models import Report


def format_json(report: Report) -> str:
    """Format report as JSON."""
    return report.model_dump_json(indent=2)

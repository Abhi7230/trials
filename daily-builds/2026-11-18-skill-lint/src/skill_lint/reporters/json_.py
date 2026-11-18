"""JSON reporter."""

import json
from typing import Any

from ..models import Report


def format_json(report: Report) -> str:
    """Format report as JSON.
    
    Args:
        report: Linting report
        
    Returns:
        JSON string
    """
    output: dict[str, Any] = {
        "version": "0.1.0",
        "results": [],
        "summary": report.summary,
    }
    
    for skill in report.skills:
        path = str(skill.path)
        findings = report.findings.get(path, [])
        score = report.scores.get(path)
        
        result = {
            "path": path,
            "name": skill.name,
            "description": skill.description,
            "score": score.model_dump() if score else None,
            "findings": [f.model_dump() for f in findings],
        }
        
        output["results"].append(result)
    
    return json.dumps(output, indent=2)

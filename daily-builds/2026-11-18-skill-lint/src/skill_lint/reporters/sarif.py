"""SARIF reporter."""

import json
from typing import Any

from ..models import Report, Severity


def format_sarif(report: Report) -> str:
    """Format report as SARIF (Static Analysis Results Interchange Format).
    
    Args:
        report: Linting report
        
    Returns:
        SARIF JSON string
    """
    # Build SARIF structure
    sarif: dict[str, Any] = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "skill-lint",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/Abhi7230/skill-lint",
                        "rules": _get_rules(),
                    }
                },
                "results": [],
            }
        ],
    }
    
    # Add results
    for skill in report.skills:
        path = str(skill.path)
        findings = report.findings.get(path, [])
        
        for finding in findings:
            result = {
                "ruleId": finding.rule_id,
                "level": _severity_to_sarif_level(finding.severity),
                "message": {
                    "text": finding.message,
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": path,
                            },
                            "region": {
                                "startLine": finding.line or 1,
                            },
                        }
                    }
                ],
            }
            
            sarif["runs"][0]["results"].append(result)
    
    return json.dumps(sarif, indent=2)


def _severity_to_sarif_level(severity: Severity) -> str:
    """Convert severity to SARIF level."""
    mapping = {
        Severity.ERROR: "error",
        Severity.WARNING: "warning",
        Severity.INFO: "note",
    }
    return mapping.get(severity, "warning")


def _get_rules() -> list[dict[str, Any]]:
    """Get rule definitions for SARIF."""
    return [
        {
            "id": "SL001",
            "shortDescription": {"text": "Missing or invalid frontmatter"},
        },
        {
            "id": "SL002",
            "shortDescription": {"text": "Name not kebab-case or doesn't match directory"},
        },
        {
            "id": "SL003",
            "shortDescription": {"text": "Description length invalid"},
        },
        {
            "id": "SL004",
            "shortDescription": {"text": "Description lacks trigger phrase"},
        },
        {
            "id": "SL005",
            "shortDescription": {"text": "Body too long"},
        },
        {
            "id": "SL006",
            "shortDescription": {"text": "Referenced file doesn't exist"},
        },
        {
            "id": "SL007",
            "shortDescription": {"text": "Broken heading hierarchy"},
        },
        {
            "id": "SL008",
            "shortDescription": {"text": "High filler phrase density"},
        },
        {
            "id": "SL009",
            "shortDescription": {"text": "No concrete examples"},
        },
        {
            "id": "SL010",
            "shortDescription": {"text": "Possible secrets detected"},
        },
        {
            "id": "SL011",
            "shortDescription": {"text": "Duplicate skill name"},
        },
    ]

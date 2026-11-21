"""Result conformance rules (RS001...)."""

from typing import Any
from jsonschema import validate, ValidationError
from ..models import Finding, Severity


def check_results(
    tool_name: str,
    result: Any,
    output_schema: Any = None
) -> list[Finding]:
    """Check tool call result conformance."""
    findings = []
    
    if isinstance(result, dict):
        if result.get("isError"):
            if "content" not in result:
                findings.append(Finding(
                    rule_id="RS001",
                    severity=Severity.WARNING,
                    message=f"tool '{tool_name}' error result missing content",
                    location=tool_name
                ))
        else:
            if "content" in result:
                content = result["content"]
                if not isinstance(content, list):
                    findings.append(Finding(
                        rule_id="RS002",
                        severity=Severity.ERROR,
                        message=f"tool '{tool_name}' content must be a list, got {type(content).__name__}",
                        location=tool_name
                    ))
                else:
                    for idx, item in enumerate(content):
                        if not isinstance(item, dict):
                            findings.append(Finding(
                                rule_id="RS003",
                                severity=Severity.ERROR,
                                message=f"tool '{tool_name}' content item {idx} must be a dict",
                                location=tool_name
                            ))
                        elif "type" not in item:
                            findings.append(Finding(
                                rule_id="RS004",
                                severity=Severity.ERROR,
                                message=f"tool '{tool_name}' content item {idx} missing type",
                                location=tool_name
                            ))
                        elif item["type"] == "text":
                            if "text" not in item:
                                findings.append(Finding(
                                    rule_id="RS005",
                                    severity=Severity.ERROR,
                                    message=f"tool '{tool_name}' text content item {idx} missing text field",
                                    location=tool_name
                                ))
                            elif not isinstance(item["text"], str):
                                findings.append(Finding(
                                    rule_id="RS006",
                                    severity=Severity.ERROR,
                                    message=f"tool '{tool_name}' text content item {idx} text must be string",
                                    location=tool_name
                                ))
            
            if output_schema and "structuredContent" in result:
                try:
                    validate(instance=result["structuredContent"], schema=output_schema)
                except ValidationError as e:
                    findings.append(Finding(
                        rule_id="RS007",
                        severity=Severity.ERROR,
                        message=f"tool '{tool_name}' structuredContent validation failed: {e.message}",
                        location=tool_name
                    ))
    
    return findings

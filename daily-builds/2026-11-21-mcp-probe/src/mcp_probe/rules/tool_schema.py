"""Tool schema conformance rules (TS001...)."""

import re
from jsonschema import Draft7Validator
from ..models import Finding, Severity, ToolInfo


TOOL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def check_tool_schemas(tools: list[ToolInfo]) -> list[Finding]:
    """Check tool schema conformance."""
    findings = []
    
    tool_names = [tool.name for tool in tools]
    if len(tool_names) != len(set(tool_names)):
        duplicates = [name for name in tool_names if tool_names.count(name) > 1]
        findings.append(Finding(
            rule_id="TS001",
            severity=Severity.ERROR,
            message=f"duplicate tool names: {set(duplicates)}"
        ))
    
    for tool in tools:
        if not TOOL_NAME_PATTERN.match(tool.name):
            findings.append(Finding(
                rule_id="TS002",
                severity=Severity.ERROR,
                message=f"tool '{tool.name}' has invalid name (must match ^[A-Za-z0-9_-]{{1,64}}$)",
                location=tool.name
            ))
        
        if not tool.description:
            findings.append(Finding(
                rule_id="TS003",
                severity=Severity.ERROR,
                message=f"tool '{tool.name}' has empty description",
                location=tool.name
            ))
        elif len(tool.description) < 20:
            findings.append(Finding(
                rule_id="TS004",
                severity=Severity.WARNING,
                message=f"tool '{tool.name}' has short description ({len(tool.description)} chars)",
                location=tool.name
            ))
        
        schema = tool.inputSchema
        
        try:
            Draft7Validator.check_schema(schema)
        except Exception as e:
            findings.append(Finding(
                rule_id="TS005",
                severity=Severity.ERROR,
                message=f"tool '{tool.name}' has invalid JSON Schema: {e}",
                location=tool.name
            ))
            continue
        
        if schema.get("type") != "object":
            findings.append(Finding(
                rule_id="TS006",
                severity=Severity.ERROR,
                message=f"tool '{tool.name}' inputSchema type must be 'object', got '{schema.get('type')}'",
                location=tool.name
            ))
        
        properties = schema.get("properties", {})
        if properties:
            for prop_name, prop_schema in properties.items():
                if "type" not in prop_schema:
                    findings.append(Finding(
                        rule_id="TS007",
                        severity=Severity.WARNING,
                        message=f"tool '{tool.name}' property '{prop_name}' missing type",
                        location=f"{tool.name}.{prop_name}"
                    ))
                
                if "description" not in prop_schema:
                    findings.append(Finding(
                        rule_id="TS008",
                        severity=Severity.WARNING,
                        message=f"tool '{tool.name}' property '{prop_name}' missing description",
                        location=f"{tool.name}.{prop_name}"
                    ))
        
        required = schema.get("required", [])
        if required:
            for req_field in required:
                if req_field not in properties:
                    findings.append(Finding(
                        rule_id="TS009",
                        severity=Severity.ERROR,
                        message=f"tool '{tool.name}' requires field '{req_field}' not in properties",
                        location=tool.name
                    ))
        
        if "additionalProperties" not in schema:
            findings.append(Finding(
                rule_id="TS010",
                severity=Severity.INFO,
                message=f"tool '{tool.name}' does not specify additionalProperties",
                location=tool.name
            ))
        
        for prop_name, prop_schema in properties.items():
            if "enum" in prop_schema:
                enum_values = prop_schema["enum"]
                if not enum_values:
                    findings.append(Finding(
                        rule_id="TS011",
                        severity=Severity.ERROR,
                        message=f"tool '{tool.name}' property '{prop_name}' has empty enum",
                        location=f"{tool.name}.{prop_name}"
                    ))
    
    return findings

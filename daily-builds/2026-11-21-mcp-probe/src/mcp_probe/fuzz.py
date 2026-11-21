"""Schema-driven input fuzzing for tool calls."""

import random
import string
from typing import Any


class FuzzGenerator:
    """Generate valid and invalid inputs from JSON Schema."""
    
    def __init__(self, seed: int = 1):
        self.rng = random.Random(seed)
    
    def generate_valid(self, schema: dict[str, Any], count: int = 4) -> list[dict[str, Any]]:
        """Generate valid inputs according to schema."""
        if schema.get("type") != "object":
            return [{}]
        
        results = []
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for _ in range(count):
            obj = {}
            
            for prop_name in required:
                if prop_name in properties:
                    obj[prop_name] = self._generate_value(properties[prop_name])
            
            for prop_name, prop_schema in properties.items():
                if prop_name not in obj and self.rng.random() < 0.5:
                    obj[prop_name] = self._generate_value(prop_schema)
            
            results.append(obj)
        
        return results
    
    def generate_invalid(self, schema: dict[str, Any], count: int = 4) -> list[dict[str, Any]]:
        """Generate invalid inputs to test error handling."""
        results = []
        
        if schema.get("type") != "object":
            return [{"invalid": True}]
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        if required:
            missing_required = {}
            for prop_name, prop_schema in properties.items():
                if prop_name not in required:
                    missing_required[prop_name] = self._generate_value(prop_schema)
            if missing_required:
                results.append(missing_required)
        
        for prop_name, prop_schema in properties.items():
            wrong_type = {prop_name: self._generate_wrong_type(prop_schema)}
            for other_prop in required:
                if other_prop != prop_name and other_prop in properties:
                    wrong_type[other_prop] = self._generate_value(properties[other_prop])
            results.append(wrong_type)
        
        if properties:
            out_of_range = {}
            can_generate_out_of_range = False
            for prop_name, prop_schema in list(properties.items())[:1]:
                out_of_range_val = self._generate_out_of_range(prop_schema)
                if out_of_range_val is not None and self._is_truly_out_of_range(prop_schema, out_of_range_val):
                    out_of_range[prop_name] = out_of_range_val
                    can_generate_out_of_range = True
            
            if can_generate_out_of_range:
                for prop_name in required:
                    if prop_name not in out_of_range and prop_name in properties:
                        out_of_range[prop_name] = self._generate_value(properties[prop_name])
                if out_of_range:
                    results.append(out_of_range)
        
        extra_field = {"__extra_unexpected_field__": "should not be here"}
        for prop_name in required:
            if prop_name in properties:
                extra_field[prop_name] = self._generate_value(properties[prop_name])
        results.append(extra_field)
        
        huge_string = {"huge": "x" * 100000}
        for prop_name in required:
            if prop_name in properties:
                huge_string[prop_name] = self._generate_value(properties[prop_name])
        results.append(huge_string)
        
        return results[:count]
    
    def _is_truly_out_of_range(self, schema: dict[str, Any], value: Any) -> bool:
        """Check if a value is truly out of range for a schema."""
        prop_type = schema.get("type", "string")
        
        if prop_type == "string" and isinstance(value, str):
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                return True
            if "minLength" in schema and len(value) < schema["minLength"]:
                return True
        elif prop_type == "integer" and isinstance(value, int):
            if "maximum" in schema and value > schema["maximum"]:
                return True
            if "minimum" in schema and value < schema["minimum"]:
                return True
        elif prop_type == "number" and isinstance(value, (int, float)):
            if "maximum" in schema and value > schema["maximum"]:
                return True
            if "minimum" in schema and value < schema["minimum"]:
                return True
        
        return False
    
    def _generate_value(self, schema: dict[str, Any]) -> Any:
        """Generate a valid value for a property schema."""
        prop_type = schema.get("type", "string")
        
        if "enum" in schema:
            enum_values = schema["enum"]
            if enum_values:
                return self.rng.choice(enum_values)
            return None
        
        if prop_type == "string":
            if "format" in schema:
                if schema["format"] == "email":
                    return "test@example.com"
                elif schema["format"] == "uri":
                    return "https://example.com"
            
            min_len = schema.get("minLength", 0)
            max_len = schema.get("maxLength", 20)
            length = self.rng.randint(max(min_len, 1), min(max_len, 20))
            return ''.join(self.rng.choices(string.ascii_letters, k=length))
        
        elif prop_type == "integer":
            minimum = schema.get("minimum", 0)
            maximum = schema.get("maximum", 100)
            return self.rng.randint(minimum, maximum)
        
        elif prop_type == "number":
            minimum = schema.get("minimum", 0.0)
            maximum = schema.get("maximum", 100.0)
            return self.rng.uniform(minimum, maximum)
        
        elif prop_type == "boolean":
            return self.rng.choice([True, False])
        
        elif prop_type == "array":
            items_schema = schema.get("items", {"type": "string"})
            min_items = schema.get("minItems", 0)
            max_items = schema.get("maxItems", 3)
            count = self.rng.randint(min_items, min(max_items, 3))
            return [self._generate_value(items_schema) for _ in range(count)]
        
        elif prop_type == "object":
            return {}
        
        return "test"
    
    def _generate_wrong_type(self, schema: dict[str, Any]) -> Any:
        """Generate a value of the wrong type."""
        prop_type = schema.get("type", "string")
        
        wrong_types = {
            "string": 12345,
            "integer": "not_a_number",
            "number": "not_a_number",
            "boolean": "not_a_bool",
            "array": "not_an_array",
            "object": "not_an_object",
        }
        
        return wrong_types.get(prop_type, None)
    
    def _generate_out_of_range(self, schema: dict[str, Any]) -> Any:
        """Generate a value outside valid range."""
        prop_type = schema.get("type", "string")
        
        if prop_type == "string" and "maxLength" in schema:
            return "x" * (schema["maxLength"] + 100)
        elif prop_type == "integer" and "maximum" in schema:
            return schema["maximum"] + 1000
        elif prop_type == "number" and "maximum" in schema:
            return schema["maximum"] + 1000.0
        
        return self._generate_value(schema)

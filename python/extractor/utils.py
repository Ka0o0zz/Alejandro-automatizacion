import re

def extract_value(pattern: str, text: str, group: int = 1) -> str:
    """
    Extract a value using a regex pattern.
    
    Args:
        pattern (str): Regex pattern to search.
        text (str): Text where to apply the pattern.
        group (int): Match group to extract.
    
    Returns:
        str: The matched value or 'NOT FOUND'.
    """
    match = re.search(pattern, text, re.IGNORECASE)
    if match and match.group(group):
        return match.group(group).strip()
    return "NOT FOUND"


def is_valid_value(value: str) -> bool:
    """
    Validate a string to determine if it's a real data field.
    
    Args:
        value (str): The value to validate.
    
    Returns:
        bool: True if valid, False if it's metadata or noise.
    """
    value = value.strip()
    if not value:
        return False
    if re.match(r"^\d+/\d+$", value):  # page numbers
        return False
    if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", value):  # dates
        return False
    if re.search(r"\d{1,2}:\d{2}", value):  # times
        return False
    if "CONSULTA" in value.upper() or "RUNT" in value.upper():
        return False
    if value.lower().startswith("http"):
        return False
    if value.endswith(":"):
        return False
    return True


def extract_fields_sequentially(text: str, fields: list[str]) -> dict:
    """
    Extracts known fields from text by looking at the next few lines.
    
    Args:
        text (str): Full document text.
        fields (list[str]): Field headers to search.
    
    Returns:
        dict: Mapping of field name to extracted value or 'NOT FOUND'.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = {field: "NOT FOUND" for field in fields}
    
    for i, line in enumerate(lines):
        key = line.strip(":").upper()
        if key in fields:
            for j in range(1, 6):  # Search next 5 lines
                if i + j < len(lines):
                    candidate = lines[i + j]
                    if is_valid_value(candidate):
                        result[key] = candidate
                        break
    return result

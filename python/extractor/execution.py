import re

def extract_execution_data(text: str) -> dict:
    """
    Extracts the execution amount from the given text.
    
    Args:
        text (str): Full text extracted from the PDF.
    
    Returns:
        dict: Dictionary with the key 'EXECUTION' and the amount as value.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "monto máximo de la obligación garantizada" in line.lower():
            # Search the next 2 lines for the amount
            for j in range(1, 3):
                if i + j < len(lines):
                    match = re.search(r"([\d\.,]+)", lines[i + j])
                    if match:
                        return {"EXECUTION": match.group(1)}
    return {"EXECUTION": "NOT FOUND"}

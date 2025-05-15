from .utils import extract_value

def extract_personal_block(text: str) -> str:
    """
    Extracts the block of personal information between 'PERSONA NATURAL' and 'PERSONA JURÍDICA'.
    
    Args:
        text (str): Full document text.
    
    Returns:
        str: Text block containing personal information.
    """
    text = text.upper()
    start = "PERSONA NATURAL: PERSONA NATURAL NACIONAL"
    end = "PERSONA JURÍDICA"

    if start in text and end in text:
        return text.split(start, 1)[1].split(end, 1)[0]
    return ""


def extract_personal_data(block: str) -> dict:
    """
    Extracts fields such as ID, full name, address, email and city from the personal info block.
    
    Args:
        block (str): Extracted personal block text.
    
    Returns:
        dict: Dictionary with keys ID_NUMBER, FULL_NAME, ADDRESS, EMAIL, CITY.
    """
    block = block.upper()
    lines = block.splitlines()

    first_name = extract_value(r"PRIMER NOMBRE\s*([A-ZÑÁÉÍÓÚ ]+)", block)
    second_name = extract_value(r"SEGUNDO NOMBRE\s*([A-ZÑÁÉÍÓÚ ]+)", block)
    last_name1 = extract_value(r"PRIMER APELLIDO\s*([A-ZÑÁÉÍÓÚ ]+)", block)
    last_name2 = extract_value(r"SEGUNDO APELLIDO\s*([A-ZÑÁÉÍÓÚ ]+)", block)

    parts = [last_name1, last_name2, first_name]
    if second_name != "NOT FOUND":
        parts.append(second_name)

    if "NOT FOUND" in parts[:3]:
        full_name = "NOT FOUND"
    else:
        full_name = " ".join(parts)

    # Address: look for the line after "DIRECCIÓN"
    address = "NOT FOUND"
    for i, line in enumerate(lines):
        if "DIRECCIÓN" in line:
            for j in range(1, 3):
                if i + j < len(lines):
                    possible = lines[i + j].strip()
                    if possible and "INCOMPL" not in possible:
                        address = possible
                        break
            break

    return {
        "EMAIL": extract_value(r"\b([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,6})\b", block),
        "ADDRESS": address,
        "FULL_NAME": full_name,
        "ID_NUMBER": extract_value(r"N[ÚU]MERO DE IDENTIFICACI[ÓO]N[:\\s]*([0-9]{6,})", block),
        "CITY": extract_value(r"MUNICIPIO\\s*([A-ZÑÁÉÍÓÚ ]+)", block)
    }

import os
import fitz  # PyMuPDF
import re
import pandas as pd
import pdfplumber
import unicodedata
import warnings

INPUT_DIR = "inputs"
OUTPUT_FILE = "outputs/datos_extraidos.xlsx"

# --- UTILIDADES DE TEXTO ---
def normalize(text: str) -> str:
    """Normaliza texto a ASCII sin acentos y en minúsculas."""
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII").lower()

def extract_text_from_pdf(path: str) -> str:
    try:
        if not path.lower().endswith(".pdf"):
            return ""
        with fitz.open(path) as doc:
            return "\n".join(page.get_text() or "" for page in doc)
    except:
        return ""

def extract_text_fallback(path: str) -> str:
    try:
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except:
        return ""

# --- SELECCIÓN DE FORMULARIO DE EJECUCIÓN ---
def get_highest_prefix_execution(folder_path: str) -> str:
    candidates = []
    for fn in os.listdir(folder_path):
        if fn.lower().endswith(".pdf") and "ejecucion" in normalize(fn):
            base = os.path.splitext(fn)[0]
            m = re.match(r"(\d+)", normalize(base))
            num = int(m.group(1)) if m else 0
            candidates.append((num, fn))
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[0])[1]

# --- EXTRACCIÓN DE EJECUCIÓN ---
def extraer_datos_ejecucion(texto: str) -> dict:
    m = re.search(r"TOTAL\s*[:：]?\s*\$?\s*([\d\.,]+)", texto, re.IGNORECASE)
    if m:
        return {"EJECUCIÓN": m.group(1).strip()}
    lines = texto.upper().splitlines()
    for i, line in enumerate(lines):
        if "DESCRIPCIÓN DEL INCUMPLIMIENTO" in line:
            for j in range(i-1, max(i-10, -1), -1):
                m2 = re.search(r"\$?\s*([\d\.,]{5,})", lines[j])
                if m2:
                    return {"EJECUCIÓN": m2.group(1).strip()}
            break
    m3 = re.search(r"EJECUCIÓN\s*[:：]?\s*\$?\s*([\d\.,]+)", texto, re.IGNORECASE)
    if m3:
        return {"EJECUCIÓN": m3.group(1).strip()}
    nums = re.findall(r"\$?\s*([\d\.,]{5,})", texto)
    cleaned = [(n, int(n.replace('.', '').replace(',', ''))) for n in nums if n.replace('.', '').replace(',', '').isdigit()]
    if cleaned:
        return {"EJECUCIÓN": max(cleaned, key=lambda x: x[1])[0].strip()}
    return {"EJECUCIÓN": "NO ENCONTRADO"}

# --- FUNCIONES ORIGINALES (RUNT, PERSONALES, FECHA) ---
def extraer_valor(patron, texto, grupo=1):
    m = re.search(patron, texto, re.IGNORECASE)
    return m.group(grupo).strip() if m and m.group(grupo) else "NO ENCONTRADO"

def es_valor_valido(posible: str) -> bool:
    s = posible.strip()
    if not s or re.match(r"^\d+\/\d+$", s) or re.search(r"\d{1,2}:\d{2}", s):
        return False
    if any(x in s.upper() for x in ["CONSULTA","RUNT"]) or s.lower().startswith("http") or s.endswith(":"):
        return False
    return True

def extraer_datos_robustos(texto: str, campos: list) -> dict:
    datos = {c: "NO ENCONTRADO" for c in campos}
    lines = [l.strip() for l in texto.upper().splitlines() if l.strip()]
    for i, ln in enumerate(lines):
        key = ln.strip(":")
        if key in campos:
            for j in range(1, 8):
                if i+j < len(lines) and es_valor_valido(lines[i+j]):
                    datos[key] = lines[i+j].strip()
                    break
    return datos

def extraer_datos_runt(texto: str) -> dict:
    antes = ["PLACA DEL VEHÍCULO","TIPO DE SERVICIO"]
    despues = ["MARCA","LÍNEA","MODELO","COLOR"]
    datos = {}
    u = texto.upper()
    if "MARCA" in u:
        a, rest = u.split("MARCA",1)
        datos.update(extraer_datos_robustos(a, antes))
        datos.update(extraer_datos_robustos("MARCA\n"+rest, despues))
    else:
        datos.update(extraer_datos_robustos(u, antes+despues))
    fmap = {"PLACA DEL VEHÍCULO":"PLACA","TIPO DE SERVICIO":"SERVICIO",
            "MARCA":"MARCA","LÍNEA":"LÍNEA","MODELO":"MODELO","COLOR":"COLOR"}
    return {fmap.get(k,k):v for k,v in datos.items()}

def extraer_bloque_deudor_por_persona(texto: str) -> str:
    """
    Extrae únicamente el bloque A.1 INFORMACIÓN SOBRE EL DEUDOR
    entre los encabezados 'A.1 INFORMACIÓN SOBRE EL DEUDOR'
    y 'B.1 INFORMACIÓN SOBRE EL ACREEDOR GARANTIZADO'.
    """
    ini = "A.1 INFORMACIÓN SOBRE EL DEUDOR"
    fin = "B.1 INFORMACIÓN SOBRE EL ACREEDOR GARANTIZADO"
    texto_u = texto.upper()
    if ini in texto_u and fin in texto_u:
        return texto_u.split(ini, 1)[1].split(fin, 1)[0]
    # Si no detecta los marcadores, cae al bloque original
    return texto_u.split(ini,1)[1].split(fin,1)[0] if ini in texto and fin in texto else texto

def extraer_datos_personales(bloque: str) -> dict:
    b = bloque.upper()
    primer_nombre = extraer_valor(r"PRIMER NOMBRE\s*([A-ZÑÁÉÍÓÚ ]+)", b)
    segundo_nombre = extraer_valor(r"SEGUNDO NOMBRE\s*([A-ZÑÁÉÍÓÚ ]+)", b)
    if segundo_nombre in ["SEXO","MASCULINO","FEMENINO"]:
        segundo_nombre = "NO ENCONTRADO"
    primer_apellido = extraer_valor(r"PRIMER APELLIDO\s*([A-ZÑÁÉÍÓÚ ]+)", b)
    segundo_apellido = extraer_valor(r"SEGUNDO APELLIDO\s*([A-ZÑÁÉÍÓÚ ]+)", b)
    partes = [primer_apellido, segundo_apellido, primer_nombre]
    if segundo_nombre != "NO ENCONTRADO": partes.append(segundo_nombre)
    nombre = " ".join([p for p in partes if p!="NO ENCONTRADO"]) if partes and all(p!="NO ENCONTRADO" for p in partes[:3]) else "NO ENCONTRADO"
    correo = extraer_valor(r"\b([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,6})\b", b)
    cedula = extraer_valor(r"NUMERO DE IDENTIFICACI[OÓ]N[:\s]*([0-9]{6,})", b)
    municipio = extraer_valor(r"MUNICIPIO\s*([A-ZÑÁÉÍÓÚ ]+)", b)
    direccion = "NO ENCONTRADO"
    for i, l in enumerate(b.splitlines()):
        if "DIRECCIÓN" in l:
            for j in (1,2):
                if i+j < len(b.splitlines()) and es_valor_valido(b.splitlines()[i+j]):
                    direccion = b.splitlines()[i+j].strip(); break
            break
    return {"NOMBRE":nombre, "CORREO":correo, "CÉDULA":cedula, "DOMICILIO":municipio, "DIRECCIÓN":direccion}

def extraer_fecha_admision(texto: str) -> dict:
    m = re.search(r"FECHA\s+ADMISI[ÓO]N\s*[:：]?\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", texto, re.IGNORECASE)
    return {"FECHA DE EJECUCIÓN": m.group(1).strip()} if m else {"FECHA DE EJECUCIÓN": "NO ENCONTRADO"}

# --- MAIN ---
def main():
    warnings.filterwarnings("ignore", message="CropBox missing from /Page")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    columnas = [
        "NÚMERO","EJECUCIÓN","FECHA DE EJECUCIÓN",
        "PLACA","MARCA","LÍNEA","MODELO","COLOR","SERVICIO",
        "CORREO","DIRECCIÓN","NOMBRE","CÉDULA","DOMICILIO",
        "PODER","CARTA ÚNICA","RGM","RUNT","PRENDA",
        "DOC_EJECUCION","DOC_ACUSE"
    ]
    registros = []
    for carpeta in sorted(os.listdir(INPUT_DIR)):
        ruta = os.path.join(INPUT_DIR, carpeta)
        if not os.path.isdir(ruta): continue
        print(f"\n📁 Procesando carpeta: {carpeta}")
        datos = {c: "NO ENCONTRADO" for c in columnas}
        datos["NÚMERO"] = carpeta
        names = " ".join(os.listdir(ruta)).lower()
        datos["PODER"] = "poder" in names
        datos["CARTA ÚNICA"] = "carta unica" in names
        datos["RGM"] = any(x in names for x in ["inscripcion inicial","formulario de inscripción inicial"])
        datos["RUNT"] = "runt" in names
        datos["PRENDA"] = "prenda" in names

        # RUNT
        for fn in os.listdir(ruta):
            path = os.path.join(ruta, fn)
            txt = extract_text_from_pdf(path)
            if not txt.strip(): txt = extract_text_fallback(path)
            if "PLACA DEL VEHÍCULO" in txt.upper():
                datos.update(extraer_datos_runt(txt))

        # EJECUCIÓN y DOC_EJECUCION
        best_fn = get_highest_prefix_execution(ruta)
        datos["DOC_EJECUCION"] = best_fn or ""
        if best_fn:
            path_exec = os.path.join(ruta, best_fn)
            txt = extract_text_from_pdf(path_exec)
            if not txt.strip(): txt = extract_text_fallback(path_exec)
            datos.update(extraer_datos_ejecucion(txt))
            bloque = extraer_bloque_deudor_por_persona(txt)
            datos.update(extraer_datos_personales(bloque))

        # FECHA y DOC_ACUSE
        acuse_fn = None
        for fn in os.listdir(ruta):
            if "acuse" in fn.lower():
                acuse_fn = fn
                path_ac = os.path.join(ruta, fn)
                txt = extract_text_from_pdf(path_ac)
                if not txt.strip(): txt = extract_text_fallback(path_ac)
                datos.update(extraer_fecha_admision(txt))
                break
        datos["DOC_ACUSE"] = acuse_fn or ""

        registros.append(datos)

    df = pd.DataFrame(registros, columns=columnas)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n✅ Datos exportados correctamente a {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

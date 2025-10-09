# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

from __future__ import annotations
import io
import re
from typing import List, Dict, Tuple

import numpy as np
from PIL import Image, ImageOps
import cv2

try:
    import pytesseract
    _TESS_AVAILABLE = True
except Exception:
    _TESS_AVAILABLE = False


# -----------------------------
# Helpers de normalización
# -----------------------------
_PRICE_PAT = re.compile(
    r"(?:(USD|US\$|\$)\s*)?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})|\d+)(?!\S)"
)
# ejemplos válidos: $5.99, 5,99, USD 12.00, 1200, 1.200,50

_TAGS_ES = {
    "vegano", "vegana", "vegetariano", "vegetariana", "sin gluten", "celiaco", "celíaco",
    "picante", "poco picante", "muy picante", "alto en sal", "alto en azúcar", "bajo en sal",
    "bajo en azúcar", "sin azúcar", "sin lactosa", "sin cebolla", "sin tomate", "salsa aparte",
    "extra queso", "extra papas"
}
_TAGS_EN = {
    "vegan", "vegetarian", "gluten-free", "celiac", "spicy", "mild", "hot",
    "high sodium", "high sugar", "low sodium", "low sugar", "no sugar",
    "lactose-free", "no onion", "no tomato", "sauce on the side", "extra cheese", "extra fries"
}


def _lang_to_tess(lang: str) -> str:
    # mapea idioma app → paquete tesseract
    return "spa" if lang.lower().startswith("es") else "eng"


def _clean_text(s: str) -> str:
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip(" :|-")


def _extract_price(text: str) -> Tuple[float, str]:
    """
    Devuelve (precio_float, resto_texto_sin_precio)
    Si no hay precio, (0.0, text)
    """
    m = _PRICE_PAT.search(text)
    if not m:
        return 0.0, text
    raw = m.group(2)
    # normalizar separadores: si contiene coma y punto, asumir punto decimal; si solo coma, usar coma decimal
    val = raw.replace(" ", "")
    if "," in val and "." in val:
        # quitar separador de miles (coma) y usar punto como decimal
        val = val.replace(",", "")
    elif "," in val and "." not in val:
        val = val.replace(".", "").replace(",", ".")
    try:
        price = float(val)
    except Exception:
        price = 0.0
    # remover el match del texto
    start, end = m.span()
    rest = (text[:start] + text[end:]).strip(" -:|")
    return price, rest


def _extract_tags(desc: str, lang: str) -> Tuple[str, str]:
    """
    Busca tags conocidos dentro de desc.
    Devuelve (tags_concatenados, desc_sin_tags)
    """
    tags = []
    pool = _TAGS_ES if lang.startswith("es") else _TAGS_EN
    lower = " " + desc.lower() + " "
    for t in pool:
        if f" {t} " in lower:
            tags.append(t)
            # quitar el tag del texto (aprox)
            desc = re.sub(re.escape(t), "", desc, flags=re.IGNORECASE)
            lower = " " + desc.lower() + " "
    clean = _clean_text(desc)
    return (", ".join(sorted(set(tags))), clean)


def _parse_line(line: str, lang: str) -> Dict:
    """
    Intenta parsear una línea:
        "Hamburguesa - $5.99 - Pan, queso, ..."
        "Agua 1.99: botella servida en vaso"
        "Duraznos al jugo $3,99 (canela)"
    """
    text = _clean_text(line)
    if not text:
        return {}

    # 1) Precio
    price, rest = _extract_price(text)

    # 2) Separar nombre vs descripción por separadores comunes
    #    Si no hay separadores, asumimos primeras 1-3 palabras como nombre si son Capitalizadas.
    name = ""
    desc = ""
    parts = re.split(r"\s[-–—|:]\s| - |: ", rest)
    if len(parts) >= 2:
        name = parts[0].strip()
        desc = " - ".join(parts[1:]).strip()
    else:
        # Heurística: primera coma/guion
        m = re.search(r"[,:-]\s", rest)
        if m:
            idx = m.start()
            name, desc = rest[:idx].strip(), rest[idx+1:].strip()
        else:
            # fallback: primera oración/primeras 3 palabras
            tokens = rest.split()
            if len(tokens) > 3:
                name = " ".join(tokens[:3])
                desc = " ".join(tokens[3:])
            else:
                name = rest
                desc = ""

    name = _clean_text(name)
    desc = _clean_text(desc)

    # 3) Tags desde descripción
    tags, desc_no_tags = _extract_tags(desc, lang)

    # sanity checks
    if not name:
        return {}

    return {
        "name": name,
        "description": desc_no_tags,
        "price": float(price) if price else 0.0,
        "special_notes": tags
    }


# -----------------------------
# Preproceso de imagen
# -----------------------------
def _load_image(file) -> Image.Image:
    if hasattr(file, "read"):
        data = file.read()
    elif isinstance(file, (bytes, bytearray)):
        data = file
    else:
        # ruta en disco
        with open(str(file), "rb") as f:
            data = f.read()
    return Image.open(io.BytesIO(data)).convert("RGB")


def _enhance_for_ocr(pil: Image.Image) -> np.ndarray:
    # Escalar (hasta ~1500px lado mayor) para mejorar OCR
    w, h = pil.size
    scale = 1500.0 / max(w, h) if max(w, h) < 1500 else 1.0
    if scale != 1.0:
        pil = pil.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

    # Aumentar contraste ligeramente
    pil = ImageOps.autocontrast(pil)

    img = np.array(pil)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Grises + denoise ligero + umbral adaptativo
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, d=7, sigmaColor=75, sigmaSpace=75)
    thr = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=33, C=10
    )
    # inversión condicional: si la mayoría es negro, invertimos
    if np.mean(thr) < 127:
        thr = 255 - thr

    return thr


# -----------------------------
# OCR principal
# -----------------------------
def _ocr_lines(img_bin: np.ndarray, tess_lang: str) -> List[str]:
    """
    Intenta usar image_to_data (con posiciones) y si falla, usa image_to_string por líneas.
    """
    config = "--oem 3 --psm 6"  # LSTM, block of text
    lines: List[str] = []

    try:
        data = pytesseract.image_to_data(
            img_bin, lang=tess_lang, config=config, output_type=pytesseract.Output.DICT)
        n = len(data.get("level", []))
        # agrupar por (block_num, par_num, line_num)
        cur_key = None
        cur_text = []
        for i in range(n):
            if int(data["conf"][i]) < 40:
                continue
            key = (data["block_num"][i], data["par_num"]
                   [i], data["line_num"][i])
            word = data["text"][i]
            if not word.strip():
                continue
            if key != cur_key:
                if cur_text:
                    lines.append(" ".join(cur_text))
                cur_key = key
                cur_text = [word]
            else:
                cur_text.append(word)
        if cur_text:
            lines.append(" ".join(cur_text))
    except Exception:
        # fallback simple
        text = pytesseract.image_to_string(
            img_bin, lang=tess_lang, config=config)
        for ln in text.splitlines():
            if ln.strip():
                lines.append(ln.strip())

    # limpieza
    lines = [_clean_text(l) for l in lines if _clean_text(l)]
    return lines


# -----------------------------
# API pública
# -----------------------------
def parse_menu_image(file, lang: str = "es") -> List[Dict]:
    """
    Lee una imagen de menú y devuelve una lista de ítems:
    [{name, description, price, special_notes}]
    """
    if not _TESS_AVAILABLE:
        raise RuntimeError(
            "Pytesseract no está disponible. Instala Tesseract OCR.\n"
            "Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "Mac (brew): brew install tesseract\n"
            "Linux (apt): sudo apt-get install tesseract-ocr tesseract-ocr-spa"
        )

    tess_lang = _lang_to_tess(lang)

    pil = _load_image(file)
    img_bin = _enhance_for_ocr(pil)
    lines = _ocr_lines(img_bin, tess_lang)

    items: List[Dict] = []
    seen = set()

    for ln in lines:
        row = _parse_line(ln, lang)
        if not row or not row["name"]:
            continue
        key = row["name"].lower()
        if key in seen:
            # merge suave: si el nuevo tiene precio o notas que antes no estaban
            for it in items:
                if it["name"].lower() == key:
                    if not it.get("price") and row.get("price"):
                        it["price"] = row["price"]
                    if row.get("special_notes"):
                        base = set([x.strip() for x in (
                            it.get("special_notes", "") or "").split(",") if x.strip()])
                        new = set([x.strip() for x in (
                            row["special_notes"] or "").split(",") if x.strip()])
                        it["special_notes"] = ", ".join(
                            sorted(base.union(new)))
                    if row.get("description") and (len(row["description"]) > len(it.get("description", ""))):
                        it["description"] = row["description"]
                    break
            continue
        seen.add(key)
        items.append(row)

    # Filtrar basura (líneas donde solo había precio o texto suelto)
    clean = [it for it in items if len(it["name"]) >= 2]

    return clean


# -----------------------------
# Formato recomendado (docstring)
# -----------------------------
RECOMMENDED_FORMAT = """
Formato recomendado para CSV/TXT/OCR:
name,description,price,special_notes
Hamburguesa,Pan, queso, carne, tomate, lechuga, cebolla y salsa de la casa,5.99,alto en sal
Agua,Botella de agua servida en vaso; con o sin hielo extra,1.99,
Duraznos al jugo,Duraznos deshuesados en almíbar con un toque de canela,3.99,vegetariano
"""

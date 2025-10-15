# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

from __future__ import annotations
from typing import List, Dict, Callable, Optional
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import uuid
import io
import os
from PIL import Image
from backend.db import MEDIA_DIR
from pathlib import Path


def fetch_banners():
    pats = ("banner_*.png", "banner_*.jpg", "banner_*.jpeg", "banner_*.webp",
            "menu_*.png", "menu_*.jpg", "menu_*.jpeg", "menu_*.webp")
    files = []
    for pat in pats:
        files += list(MEDIA_DIR.glob(pat))
    # devuelve strings para el carrusel
    return [str(p) for p in sorted(files)]


# def _img_to_base64(img_path: str) -> str | None:
#     try:
#         p = img_path
#         if not os.path.isabs(p):
#             p = os.path.abspath(p)
#         if not os.path.isfile(p):
#             return None
#         im = Image.open(p).convert("RGB")
#         buf = io.BytesIO()
#         im.save(buf, format="PNG")
#         b64 = base64.b64encode(buf.getvalue()).decode("ascii")
#         return f"data:image/png;base64,{b64}"
#     except Exception:
#         return None

def _img_to_base64(img_path: str) -> str | None:
    try:
        p = img_path
        if not os.path.isabs(p):
            p = os.path.abspath(p)
        if not os.path.isfile(p):
            # Diagnóstico útil en Cloud
            st.caption(f"⚠️ No existe la imagen: {p}")
            return None
        im = Image.open(p).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        st.caption(f"⚠️ No se pudo abrir la imagen: {img_path} · {e}")
        return None


# --- normalizador cross-platform (útil también para imágenes)
def _normalize_path(p: str) -> str:
    if not p:
        return p
    p = p.replace("\\", "/")             # Windows -> Linux
    if not os.path.isabs(p) and not p.startswith("data/media/"):
        p = os.path.join("data", "media", os.path.basename(p))
    p = os.path.normpath(p)
    if not os.path.isabs(p):
        p = os.path.abspath(p)
    return p


def _img_to_base64_quiet(img_path: str) -> str | None:
    try:
        p = _normalize_path(img_path)
        if not os.path.isfile(p):
            return None
        im = Image.open(p).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None


# def render_js_carousel(
#     images: list[str] | list[Image.Image],
#     interval_ms: int = 5000,
#     aspect_ratio: float = 16/9,
#     key_prefix: str = "carousel",
#     show_dots: bool = True,
#     height_px: int | None = None,   # ← NUEVO parámetro (opcional)
#     **kwargs,                       # ← para seguir siendo compatible
# ):
#     """
#     Muestra un carrusel puro JS/HTML, sin provocar reruns de Streamlit.
#     - height_px: si se pasa, fuerza alto fijo en px. Si no, usa aspect_ratio.
#     """
#     if not images:
#         st.info("No hay imágenes para mostrar.")
#         return

#     # convierte a data URLs
#     data_urls = []
#     for img in images:
#         if isinstance(img, str):
#             b64 = _img_to_base64_quiet(img)
#         else:
#             buf = io.BytesIO()
#             img.save(buf, format="PNG")
#             b64 = "data:image/png;base64," + \
#                 base64.b64encode(buf.getvalue()).decode("ascii")
#         if b64:
#             data_urls.append(b64)

#     if not data_urls:
#         st.warning("No se pudieron cargar las imágenes del carrusel.")
#         return

#     # HTML/JS del carrusel
#     height_style = f"height:{
#         int(height_px)}px;" if height_px else f"aspect-ratio:{aspect_ratio};"
#     dots_html = ""
#     if show_dots:
#         dots_html = "<div class='dots'>" + "".join(
#             f"<span class='dot' data-idx='{i}'></span>" for i in range(len(data_urls))
#         ) + "</div>"

#     html = f"""
#     <style>
#       .carousel-{key_prefix} {{
#         width: 100%; {height_style}
#         position: relative; overflow: hidden; border-radius: 12px; background: #111;
#         display:flex; align-items:center; justify-content:center;
#       }}
#       .carousel-{key_prefix} img {{
#         width: 100%; height: 100%; object-fit: cover;
#       }}
#       .dots {{
#         position: absolute; bottom: 8px; width: 100%; text-align: center;
#       }}
#       .dot {{
#         display: inline-block; width: 8px; height: 8px; border-radius: 50%;
#         background: #bbb; margin: 0 4px; cursor: pointer;
#       }}
#       .dot.active {{ background: #fff; }}
#     </style>
#     <div class="carousel-{key_prefix}">
#       <img id="{key_prefix}-img" src="{data_urls[0]}" />
#       {dots_html}
#     </div>
#     <script>
#       (function(){{
#         const imgs = {data_urls};
#         const img = parent.document.getElementById("{key_prefix}-img");
#         const dots = parent.document.querySelectorAll(".carousel-{key_prefix} .dot");
#         let idx = 0;
#         function show(i){{
#           idx = (i + imgs.length) % imgs.length;
#           img.src = imgs[idx];
#           dots.forEach((d,j)=>d.classList.toggle("active", j===idx));
#         }}
#         dots.forEach(d => {{
#           d.addEventListener('click', ()=> show(parseInt(d.getAttribute('data-idx'))));
#         }});
#         show(0);
#         setInterval(()=> show(idx+1), {int(interval_ms)});
#       }})();
#     </script>
#     """
#     st.markdown(html, unsafe_allow_html=True)


def render_js_carousel(
    images, interval_ms: int = 5000, aspect_ratio: float = 16/9,
    key_prefix: str = "carousel", show_dots: bool = True, height_px: int | None = None, **_
):
    if not images:
        st.info("No hay imágenes para mostrar.")
        return

    data_urls = []
    for img in images:
        if isinstance(img, str):
            b64 = _img_to_base64_quiet(img)
        else:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = "data:image/png;base64," + \
                base64.b64encode(buf.getvalue()).decode("ascii")
        if b64:
            data_urls.append(b64)

    if not data_urls:
        st.warning("No se pudieron cargar las imágenes del carrusel.")
        return

    height_style = f"height:{
        int(height_px)}px;" if height_px else f"aspect-ratio:{aspect_ratio};"
    dots_html = ""
    if show_dots and len(data_urls) > 1:
        dots_html = "<div class='dots'>" + "".join(
            f"<span class='dot' data-idx='{i}'></span>" for i in range(len(data_urls))
        ) + "</div>"

    html = f"""
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        body {{ margin:0; padding:0; background:transparent; }}
        .carousel-{key_prefix} {{
          width: 100%; {height_style}
          position: relative; overflow: hidden; border-radius: 12px; background: #111;
          display:flex; align-items:center; justify-content:center;
        }}
        .carousel-{key_prefix} img {{
          width: 100%; height: 100%; object-fit: cover;
        }}
        .dots {{
          position: absolute; bottom: 8px; width: 100%; text-align: center;
        }}
        .dot {{
          display: inline-block; width: 8px; height: 8px; border-radius: 50%;
          background: #bbb; margin: 0 4px; cursor: pointer;
        }}
        .dot.active {{ background: #fff; }}
      </style>
    </head>
    <body>
      <div class="carousel-{key_prefix}">
        <img id="{key_prefix}-img" src="{data_urls[0]}" />
        {dots_html}
      </div>
      <script>
        (function(){{
          const imgs = {data_urls};
          const img = document.getElementById("{key_prefix}-img");
          const dots = document.querySelectorAll(".carousel-{key_prefix} .dot");
          let idx = 0;

          function show(i){{
            idx = (i + imgs.length) % imgs.length;
            img.src = imgs[idx];
            if (dots && dots.length) {{
              dots.forEach((d,j)=>d.classList.toggle("active", j===idx));
            }}
          }}

          if (dots && dots.length) {{
            dots.forEach(d => {{
              d.addEventListener('click', ()=> show(parseInt(d.getAttribute('data-idx'))));
            }});
          }}

          show(0);
          if (imgs.length > 1) {{
            setInterval(()=> show(idx+1), {int(interval_ms)});
          }}
        }})();
      </script>
    </body>
    </html>
    """
    # Usa components.html para aislar el JS y fijar altura del iframe
    iframe_h = height_px if height_px else int(600 / (16/9))  # valor seguro
    components.html(html, height=iframe_h, scrolling=False)


def _image(img, **kwargs):
    try:
        # Si es string (ruta), valida existencia y usa PIL para abrir
        if isinstance(img, str):
            p = img
            if not os.path.isabs(p):
                p = os.path.abspath(p)
            if not os.path.isfile(p):
                st.warning(f"No se encontró la imagen: {img}")
                return
            try:
                im = Image.open(p)
            except Exception:
                st.warning(f"No se pudo abrir la imagen: {img}")
                return
            try:
                return st.image(im, width='stretch', **{k: v for k, v in kwargs.items() if k != "width"})
            except TypeError:
                return st.image(im, use_column_width=True)
        else:
            # objeto PIL/ndarray/bytes
            try:
                return st.image(img, width='stretch', **{k: v for k, v in kwargs.items() if k != "width"})
            except TypeError:
                return st.image(img, use_column_width=True)
    except Exception:
        st.warning("No se pudo renderizar la imagen.")


def _button(label: str, key: Optional[str] = None):
    return st.button(label, key=key)


def menu_table_component(
    menu: List[Dict],
    lang: str = "es",
    deletable: bool = False,
    on_delete: Optional[Callable[[str], None]] = None,
):
    if not menu:
        st.info("No hay ítems de menú." if lang == "es" else "No menu items.")
        return
    df = pd.DataFrame([{
        "id": m.get("id"),
        "Nombre" if lang == "es" else "Name": m.get("name", ""),
        "Descripción" if lang == "es" else "Description": m.get("description", ""),
        "Precio" if lang == "es" else "Price": f'{m.get("currency", "")} {float(m.get("price", 0.0)):.2f}',
        "Notas" if lang == "es" else "Notes": m.get("special_notes", ""),
    } for m in menu])
    try:
        st.dataframe(df, width='stretch', hide_index=True)
    except TypeError:
        st.dataframe(df)

    if deletable and on_delete:
        st.markdown("---")
        st.caption("Eliminar ítem del menú" if lang ==
                   "es" else "Delete menu item")
        ids = [m.get("id") for m in menu if m.get("id") is not None]
        if ids:
            sel = st.selectbox("ID", ids, key="menu_delete_id")
            if _button("Borrar" if lang == "es" else "Delete", key="btn_delete_menu"):
                try:
                    on_delete(sel)
                    st.success("Ítem eliminado." if lang ==
                               "es" else "Item deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(("No se pudo eliminar: " if lang ==
                             "es" else "Failed to delete: ") + str(e))


def menu_gallery_component(
    menu: List[Dict],
    lang: str = "es",
    images: Optional[List[str]] = None,
    columns: int = 2,
):
    if not menu and not images:
        st.info("No hay elementos para mostrar." if lang ==
                "es" else "Nothing to show.")
        return
    if images:
        if columns < 1:
            columns = 1
        for i in range(0, len(images), columns):
            row = st.columns(columns)
            for j, col in enumerate(row):
                k = i + j
                if k < len(images):
                    with col:
                        _image(images[k])
    if menu:
        for m in menu:
            name = m.get("name", "")
            price = f'{m.get("currency", "")} {float(m.get("price", 0.0)):.2f}'
            notes = m.get("special_notes", "")
            desc = m.get("description", "")
            st.markdown(f"**{name}** — {price}")
            if notes:
                st.caption(notes)
            if desc:
                st.write(desc)
            st.write("")

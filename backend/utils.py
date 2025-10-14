# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

from __future__ import annotations
from typing import List, Dict, Callable, Optional
import streamlit as st
import pandas as pd
import base64
import uuid
import io
import os
from PIL import Image


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


def _img_to_base64_quiet(img_path: str) -> str | None:
    try:
        p = img_path if os.path.isabs(img_path) else os.path.abspath(img_path)
        if not os.path.isfile(p):
            return None
        im = Image.open(p).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None


def render_js_carousel(
    image_paths,
    interval_ms: int = 5000,
    aspect_ratio: float = 16/6,
    key_prefix: str = "carousel",
    show_dots: bool = True,
    *args, **kwargs
):
    """
    Retrocompatible: si versiones antiguas lo llaman sin height_px, no rompe.
    height_px opcional en kwargs.
    """
    height_px = kwargs.pop("height_px", None)
    if not image_paths:
        st.info("No hay imágenes para el carrusel.")
        return

    data_uris, missing = [], 0
    for p in image_paths:
        b64 = _img_to_base64_quiet(p)
        if b64:
            data_uris.append(b64)
        else:
            missing += 1

    if not data_uris:
        st.info("No se pudieron cargar imágenes del carrusel.")
        return
    elif missing > 0:
        st.caption(f"Se omitieron {missing} imagen(es) no disponibles.")

    cid = f"c_{key_prefix}_{uuid.uuid4().hex[:8]}"
    dots_html = ""
    if show_dots:
        dots_html = "<div class='dots'>" + \
            "".join(
                [f"<span class='dot' data-idx='{i}'></span>" for i in range(len(data_uris))]) + "</div>"

    html = f"""
        <div id="{cid}" class="carousel">
          <div class="viewport">
            {''.join([f'<img class="slide" src="{u}" loading="lazy" />' for u in data_uris])}
          </div>
          {dots_html}
        </div>

        <style>
          #{cid}.carousel {{
            width: 100%;
            max-width: 1200px;
            margin: .25rem auto 0 auto;
          }}
          #{cid} .viewport {{
            position: relative;
            width: 100%;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.08);
            height: {height_px if height_px else 'auto'}px;
          }}
          #{cid} .viewport::before {{
            content: "";
            display: {"none" if height_px else "block"};
            padding-top: {0 if height_px else f"{100/aspect_ratio:.4f}%"};
          }}
          #{cid} .viewport .slide {{
            position: absolute; top:0; left:0;
            width: 100%; height: 100%;
            object-fit: cover; display: none;
          }}
          #{cid} .viewport .slide.active {{ display: block; }}
          #{cid} .dots {{
            display: flex; gap: 8px; justify-content: center; align-items: center;
            margin-top: .5rem;
          }}
          #{cid} .dot {{
            width: 10px; height: 10px; border-radius: 50%;
            background: #d0d0d0; cursor: pointer;
          }}
          #{cid} .dot.active {{ background: #4a90e2; }}
          @media (max-width: 768px) {{
            #{cid}.carousel {{ max-width: 100%; }}
            #{cid} .viewport {{ height: {int((height_px or 420)*0.9)}px; }}
          }}
        </style>

        <script>
          (function() {{
            const root = document.getElementById("{cid}");
            if (!root) return;
            const slides = Array.from(root.querySelectorAll(".slide"));
            const dots = Array.from(root.querySelectorAll(".dot"));
            let idx = 0;
            function show(i) {{
              slides.forEach((el, k) => el.classList.toggle("active", k===i));
              dots.forEach((el, k) => el.classList.toggle("active", k===i));
            }}
            function next() {{ idx = (idx + 1) % slides.length; show(idx); }}
            if (slides.length) show(0);
            let timer = setInterval(next, {interval_ms});
            dots.forEach(d => {{
              d.addEventListener('click', () => {{
                const i = parseInt(d.getAttribute('data-idx'));
                idx = i; show(idx);
                clearInterval(timer);
                timer = setInterval(next, {interval_ms});
              }});
            }});
          }})();
        </script>
    """
    comp_height = height_px or int(900/aspect_ratio)
    st.components.v1.html(html, height=comp_height + 60, scrolling=False)


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

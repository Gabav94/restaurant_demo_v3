# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:37:32 2025

@author: geam9
"""

# from __future__ import annotations
# import streamlit as st
# from uuid import uuid4
# from streamlit_webrtc import webrtc_streamer, WebRtcMode
# import av
# import numpy as np
# from backend.utils import render_js_carousel

# from backend.config import get_config
# from backend.db import (
#     fetch_menu, fetch_menu_banners, create_order_from_chat_ready,
#     fetch_menu_images
# )
# from backend.llm_chat import (
#     client_assistant_reply, extract_client_info, ensure_all_required_present,
#     parse_items_from_chat, client_voice_to_text
# )
# from backend.utils import menu_table_component, menu_gallery_component
# import time


# def carousel(images: list[str], key_prefix: str, lang: str, interval_sec: int = 5):
#     if "carousel_state" not in st.session_state:
#         st.session_state.carousel_state = {}
#     state = st.session_state.carousel_state.setdefault(
#         key_prefix, {"idx": 0, "on": True})

#     # Toggle y avance
#     colA, colB = st.columns([1, 3])
#     with colA:
#         state["on"] = st.toggle(
#             "⏯️ Auto", value=state["on"], key=f"{key_prefix}_auto")
#     with colB:
#         st.caption("Avanza cada 5s" if lang == "es" else "Advances every 5s")

#     if images:
#         from backend.utils import _image  # usa tu helper
#         _image(images[state["idx"]])

#         # Controles manuales
#         c1, c2, c3 = st.columns(3)
#         if c1.button("⏮️", key=f"{key_prefix}_prev"):
#             state["idx"] = (state["idx"]-1) % len(images)
#             st.rerun()
#         if c3.button("⏭️", key=f"{key_prefix}_next"):
#             state["idx"] = (state["idx"]+1) % len(images)
#             st.rerun()

#         # Autoavance simple por refresh
#         if state["on"]:
#             # Inyecta refresh a los 5s SIN tocar toda la app (solo recarga la página)
#             st.markdown(
#                 f"<meta http-equiv='refresh' content='{interval_sec}'>",
#                 unsafe_allow_html=True
#             )
#             # al volver a correr, avanzamos índice
#             state["idx"] = (state["idx"]+1) % len(images)


# st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

# st.markdown("""
# <style>
# /* Caja de chat con scroll interno */
# .chat-box {
#   border: 1px solid #eee; border-radius: 12px;
#   padding: 10px 12px; height: 52vh; overflow-y: auto;
#   background: #fafafa;
# }
# /* Burbujas estilo WhatsApp */
# .msg-user { background:#DCF8C6; color:#222; padding:10px 12px; border-radius:14px; margin:6px 0; max-width:88%; align-self:flex-end; }
# .msg-bot  { background:#ffffff; color:#222; padding:10px 12px; border-radius:14px; margin:6px 0; max-width:88%; align-self:flex-start; border:1px solid #eee; }
# /* Pie con input */
# .input-row { position: sticky; bottom: 0; background: #fff; padding-top: 8px; }
# @media (max-width: 768px){
#   .chat-box { height: 54vh; }
# }
# </style>
# """, unsafe_allow_html=True)


# def _t(lang):
#     return (lambda es, en: es if lang == "es" else en)


# def _image_compat(img):
#     try:
#         st.image(img, width='stretch')
#     except TypeError:
#         st.image(img, use_column_width=True)


# def main():
#     cfg = get_config()
#     lang = cfg.get("language", "es")
#     t = _t(lang)
#     currency = cfg.get("currency", "USD")

#     st.title(t("💬 Cliente", "💬 Client"))

#     # banners = fetch_menu_banners()
#     # if banners:
#     #     _image_compat(banners[0])

#     menu = fetch_menu()
#     if not menu:
#         st.warning(t("El restaurante aún no ha cargado su menú.",
#                    "The restaurant has not uploaded its menu yet."))
#         return

#     if "conv_id" not in st.session_state:
#         st.session_state.conv_id = uuid4().hex
#     if "conv" not in st.session_state:
#         st.session_state.conv = [{"role": "assistant", "content": t(
#             "Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
#             "Thanks for contacting us. How can we help?"
#         )}]
#     if "client_info" not in st.session_state:
#         st.session_state.client_info = {}
#     if "order_items" not in st.session_state:
#         st.session_state.order_items = []

#     view = st.radio(t("Visualización del menú", "Menu view"), [
#                     t("Tabla", "Table"), t("Imágenes", "Images")], horizontal=True)
#     col_menu, col_chat = st.columns([1, 1])

#     with col_menu:
#         st.subheader(t("📖 Menú", "📖 Menu"))
#         if view == t("Tabla", "Table"):
#             menu_table_component(menu, lang)
#         else:
#             gallery = fetch_menu_images()
#             if not gallery:
#                 st.info(t("No hay imágenes cargadas aún.",
#                         "No images uploaded yet."))
#             else:
#                 # menu_gallery_component(menu, lang, images=gallery, columns=2)
#                 # carousel(gallery, key_prefix="client_menu",
#                 #          lang=lang, interval_sec=5)
#                 render_js_carousel(gallery, interval_ms=5000, aspect_ratio=16 /
#                                    6, key_prefix="client_menu", show_dots=True, height_px=420)

#     with col_chat:
#         st.subheader("💬 Chat")
#         for m in st.session_state.conv:
#             klass = "user-bubble" if m["role"] == "user" else "bot-bubble"
#             with st.chat_message(m["role"]):
#                 st.markdown(f'<div class="{klass}">{
#                             m["content"]}</div>', unsafe_allow_html=True)

#         user_msg = st.chat_input(
#             t("Escribe tu mensaje…", "Type your message…"))

#         rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
#         media_constraints = {"audio": True, "video": False}
#         webrtc_ctx = webrtc_streamer(
#             key="client-ptt",
#             mode=WebRtcMode.SENDONLY,
#             rtc_configuration=rtc_cfg,
#             media_stream_constraints=media_constraints,
#             audio_receiver_size=256,
#             async_processing=True,
#         )

#         if "audio_buffer" not in st.session_state:
#             st.session_state.audio_buffer = []

#         class AudioProcessor:
#             def recv(self, frame: av.AudioFrame):
#                 pcm = frame.to_ndarray()
#                 st.session_state.audio_buffer.append(pcm)
#                 return frame

#         if webrtc_ctx and webrtc_ctx.state.playing:
#             webrtc_ctx.audio_processor = AudioProcessor()

#         if st.button(t("🎙️ Usar último audio", "🎙️ Use last audio")) and st.session_state.audio_buffer:
#             wav_bytes = np.concatenate(
#                 st.session_state.audio_buffer, axis=1).tobytes()
#             st.session_state.audio_buffer = []
#             text = client_voice_to_text(wav_bytes, cfg)
#             if text:
#                 user_msg = (user_msg + " " if user_msg else "") + text

#         if user_msg:
#             st.session_state.conv.append({"role": "user", "content": user_msg})
#             reply = client_assistant_reply(
#                 st.session_state.conv, menu, cfg, conversation_id=st.session_state.conv_id)
#             st.session_state.conv.append(
#                 {"role": "assistant", "content": reply})

#             info = extract_client_info(st.session_state.conv, lang)
#             st.session_state.client_info.update(
#                 {k: v for k, v in info.items() if v})
#             st.session_state.order_items = parse_items_from_chat(
#                 st.session_state.conv, menu, cfg)

#             # Nueva lógica: si falta info, preguntar explícitamente el siguiente campo
#             missing = ensure_all_required_present(
#                 st.session_state.client_info, lang)
#             if missing:
#                 next_field = missing[0]
#                 q_map_es = {
#                     "name": "¿Cuál es tu nombre?",
#                     "phone": "¿Cuál es tu número de teléfono?",
#                     "delivery_type": "¿Será para recoger (pickup) o entrega a domicilio?",
#                     "address": "¿Cuál es la dirección para la entrega?",
#                     "pickup_eta_min": "¿En cuántos minutos pasarías a recoger?",
#                     "payment_method": "¿Cuál es tu método de pago (efectivo, tarjeta u online)?",
#                 }
#                 q_map_en = {
#                     "name": "What is your name?",
#                     "phone": "What is your phone number?",
#                     "delivery_type": "Pickup or delivery?",
#                     "address": "What is the delivery address?",
#                     "pickup_eta_min": "In how many minutes would you pick up?",
#                     "payment_method": "What is your payment method (cash, card, online)?",
#                 }
#                 qmap = q_map_es if lang == "es" else q_map_en
#                 st.session_state.conv.append(
#                     {"role": "assistant", "content": qmap[next_field]})

#             st.rerun()

#     st.write("---")
#     missing = ensure_all_required_present(
#         st.session_state.get("client_info", {}), lang)
#     label_map_es = {"name": "nombre", "phone": "teléfono", "delivery_type": "tipo de entrega",
#                     "payment_method": "método de pago", "address": "dirección", "pickup_eta_min": "tiempo de retiro (min)"}
#     label_map_en = {"name": "name", "phone": "phone", "delivery_type": "delivery type",
#                     "payment_method": "payment method", "address": "address", "pickup_eta_min": "pickup ETA (min)"}
#     lm = label_map_es if lang == "es" else label_map_en
#     miss_str = ", ".join([lm[m] for m in missing])

#     left, right = st.columns([2, 1])
#     with left:
#         if missing:
#             st.warning((f"Faltan datos para confirmar: {
#                        miss_str}." if lang == "es" else f"Missing fields: {miss_str}."))
#         else:
#             st.success(t("Tenemos todos los datos. Puedes confirmar.",
#                        "All data present. You can confirm."))
#             if st.session_state.get("order_items"):
#                 st.caption(t("Items detectados: ", "Detected items: ") + "; ".join(
#                     [f"{i['name']} x{i['qty']}" for i in st.session_state["order_items"]]))

#     with right:
#         if st.button(t("✅ Confirmar pedido", "✅ Confirm order")):
#             if missing:
#                 st.error((f"No se puede confirmar. Falta: {
#                          miss_str}" if lang == "es" else f"Cannot confirm. Missing: {miss_str}"))
#             else:
#                 order = create_order_from_chat_ready(
#                     client=st.session_state.get("client_info", {}),
#                     items=st.session_state.get("order_items", []),
#                     currency=currency,
#                 )
#                 st.session_state.conv.append({"role": "assistant", "content": t(
#                     "Pedido confirmado. ¡Lo estamos preparando! 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
#                     "Order confirmed. We’re on it! 🚗💨 for delivery, or ready at your pickup time."
#                 )})
#                 st.success(t("¡Pedido confirmado!", "Order confirmed!"))
#                 st.rerun()


# if __name__ == "__main__":
#     main()

# # -*- coding: utf-8 -*-
# from __future__ import annotations
# import streamlit as st
# from uuid import uuid4
# from streamlit_webrtc import webrtc_streamer, WebRtcMode
# import av
# import numpy as np

# from backend.utils import render_js_carousel, menu_table_component
# from backend.config import get_config
# from backend.db import (
#     fetch_menu, create_order_from_chat_ready, fetch_menu_images
# )
# from backend.llm_chat import (
#     client_assistant_reply, extract_client_info, ensure_all_required_present,
#     parse_items_from_chat, client_voice_to_text
# )

# # ──────────────────────────────────────────────────────────────────────────────
# # Config de página
# # ──────────────────────────────────────────────────────────────────────────────
# st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

# # CSS: chat estilo WhatsApp con avatares, azul (bot) e verde (cliente)
# st.markdown("""
# <style>
# .chat-box {
#   border: 1px solid var(--secondary-background-color, #eee);
#   border-radius: 12px;
#   padding: 10px 12px; height: 52vh; overflow-y: auto;
#   background: var(--background-color);
#   display: flex; flex-direction: column; gap: 8px;
# }
# .msg-row { display: flex; align-items: flex-end; gap: 8px; }
# .msg-row.left  { justify-content: flex-start; }
# .msg-row.right { justify-content: flex-end; }

# .avatar {
#   width: 28px; height: 28px; border-radius: 50%;
#   display: inline-flex; align-items: center; justify-content: center;
#   font-size: 16px; color: #fff; user-select: none;
# }
# .avatar-bot  { background: #1f6feb; }   /* azul */
# .avatar-user { background: #22c55e; }   /* verde */

# .bubble {
#   max-width: 88%;
#   padding: 10px 12px; border-radius: 14px;
#   box-shadow: 0 1px 2px rgba(0,0,0,.06);
#   color: #0f172a; line-height: 1.35;
#   border: 1px solid rgba(0,0,0,0.06);
#   word-wrap: break-word; white-space: pre-wrap;
# }
# .bubble.bot  { background: #e6f0ff; border-color: #cfe2ff; }
# .bubble.user { background: #eafcf1; border-color: #ccf5db; }

# .header-chip {
#   font-size: 11px; font-weight: 600; margin-bottom: 4px;
#   color: #0b3d91;
# }

# .input-row { position: sticky; bottom: 0; background: #fff; padding-top: 8px; }
# @media (max-width: 768px){
#   .chat-box { height: 56vh; }
# }
# </style>
# """, unsafe_allow_html=True)


# def _t(lang: str):
#     return (lambda es, en: es if lang == "es" else en)


# def main():
#     cfg = get_config()
#     lang = cfg.get("language", "es")
#     t = _t(lang)
#     currency = cfg.get("currency", "USD")
#     assistant_name = cfg.get(
#         "assistant_name", "Asistente" if lang == "es" else "Assistant")

#     st.title(t("💬 Cliente", "💬 Client"))

#     # Menú
#     menu = fetch_menu()
#     if not menu:
#         st.warning(t("El restaurante aún no ha cargado su menú.",
#                      "The restaurant has not uploaded its menu yet."))
#         return

#     # Estado
#     ss = st.session_state
#     if "conv_id" not in ss:
#         ss.conv_id = uuid4().hex
#     if "conv" not in ss:
#         ss.conv = [{
#             "role": "assistant",
#             "content": t("Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
#                          "Thanks for contacting us. How can we help?")
#         }]
#     if "client_info" not in ss:
#         ss.client_info = {}
#     if "order_items" not in ss:
#         ss.order_items = []
#     if "pending_user_input" not in ss:
#         ss.pending_user_input = ""
#     # Fase para preguntar datos luego de tener pedido (y total)
#     if "collecting_info" not in ss:
#         ss.collecting_info = False
#     if "next_field_idx" not in ss:
#         ss.next_field_idx = 0

#     # Vista: tabla o imágenes
#     view = st.radio(
#         t("Visualización del menú", "Menu view"),
#         [t("Tabla", "Table"), t("Imágenes", "Images")],
#         horizontal=True
#     )

#     col_menu, col_chat = st.columns([1, 1])

#     # ── Menú (izquierda)
#     with col_menu:
#         st.subheader(t("📖 Menú", "📖 Menu"))
#         if view == t("Tabla", "Table"):
#             menu_table_component(menu, lang)
#         else:
#             gallery = fetch_menu_images()
#             if not gallery:
#                 st.info(t("No hay imágenes cargadas aún.",
#                         "No images uploaded yet."))
#             else:
#                 render_js_carousel(
#                     gallery, interval_ms=5000, aspect_ratio=16/7,
#                     key_prefix="client_menu", show_dots=True, height_px=420
#                 )

#     # ── Chat (derecha)
#     with col_chat:
#         st.markdown('<div class="chat-box" id="chatBox">',
#                     unsafe_allow_html=True)
#         for m in ss.conv:
#             if m["role"] == "user":
#                 st.markdown(
#                     f"""
#                     <div class="msg-row right">
#                       <div class="bubble user"><div class="header-chip">🙂 {t("Cliente", "Customer")}</div>{m["content"]}</div>
#                       <div class="avatar avatar-user">🙂</div>
#                     </div>
#                     """,
#                     unsafe_allow_html=True
#                 )
#             else:
#                 st.markdown(
#                     f"""
#                     <div class="msg-row left">
#                       <div class="avatar avatar-bot">🤖</div>
#                       <div class="bubble bot"><div class="header-chip">{assistant_name}</div>{m["content"]}</div>
#                     </div>
#                     """,
#                     unsafe_allow_html=True
#                 )
#         st.markdown('</div>', unsafe_allow_html=True)

#         # WebRTC (audio)
#         rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
#         media_constraints = {"audio": True, "video": False}
#         webrtc_ctx = webrtc_streamer(
#             key="client-ptt",
#             mode=WebRtcMode.SENDONLY,
#             rtc_configuration=rtc_cfg,
#             media_stream_constraints=media_constraints,
#             audio_receiver_size=256,
#             async_processing=True,
#         )

#         if "audio_buffer" not in ss:
#             ss.audio_buffer = []

#         class AudioProcessor:
#             def recv(self, frame: av.AudioFrame):
#                 pcm = frame.to_ndarray()
#                 ss.audio_buffer.append(pcm)
#                 return frame

#         if webrtc_ctx and webrtc_ctx.state.playing:
#             webrtc_ctx.audio_processor = AudioProcessor()

#         # Input fijo inferior: texto | Enviar | Confirmar | 🎙️
#         st.markdown('<div class="input-row">', unsafe_allow_html=True)
#         c1, c2, c3, c4 = st.columns([7, 1.5, 2, 1.5])

#         user_text = c1.text_input(
#             "message",
#             value=ss.get("pending_user_input", ""),
#             key="client_input",
#             placeholder=t("Escribe tu mensaje…", "Type your message…"),
#             label_visibility="collapsed"
#         )
#         send_clicked = c2.button(t("Enviar", "Send"), use_container_width=True)

#         # Confirmar: solo habilitado cuando NO falte info
#         missing = ensure_all_required_present(ss.get("client_info", {}), lang)
#         confirm_disabled = bool(missing)
#         confirm_clicked = c3.button(
#             t("Confirmar", "Confirm"),
#             use_container_width=True,
#             disabled=confirm_disabled
#         )
#         mic_clicked = c4.button("🎙️", use_container_width=True)

#         # Mic → transcribir último audio acumulado
#         if mic_clicked and ss.audio_buffer:
#             wav_bytes = np.concatenate(ss.audio_buffer, axis=1).tobytes()
#             ss.audio_buffer = []
#             text = client_voice_to_text(wav_bytes, cfg)
#             if text:
#                 cur = ss.get("pending_user_input", "")
#                 ss.pending_user_input = (cur + " " + text).strip()
#                 st.rerun()

#         # Enviar mensaje al LLM
#         if send_clicked and user_text.strip():
#             ss.conv.append({"role": "user", "content": user_text.strip()})
#             ss.pending_user_input = ""

#             reply = client_assistant_reply(
#                 ss.conv, menu, cfg, conversation_id=ss.conv_id
#             )
#             ss.conv.append({"role": "assistant", "content": reply})

#             # Parseo de items + info
#             info = extract_client_info(ss.conv, lang)
#             ss.client_info.update({k: v for k, v in info.items() if v})
#             ss.order_items = parse_items_from_chat(ss.conv, menu, cfg)

#             # --- NUEVO: trigger robusto para iniciar fase de datos ---
#             def _looks_like_total_or_close(reply_text: str, user_text: str) -> bool:
#                 r = (reply_text or "").lower()
#                 u = (user_text or "").lower()
#                 money_signals = ["total", "subtotal", "precio", "price",
#                                  "$", "usd", "eur", "s/.", "mxn", "cop", "ars"]
#                 close_signals = [
#                     "eso sería todo", "listo", "está bien", "confirmar", "confirmo",
#                     "that's all", "done", "ok that's it", "confirm"
#                 ]
#                 if any(s in r for s in money_signals):
#                     return True
#                 if any(s in u for s in close_signals):
#                     return True
#                 return False

#             last_assistant = next((m["content"] for m in reversed(
#                 ss.conv) if m["role"] == "assistant"), "")
#             # user_text de este turno lo tienes como `user_text`
#             should_collect = (ss.order_items and _looks_like_total_or_close(
#                 last_assistant, user_text))

#             if should_collect and not ss.collecting_info:
#                 pre = ("Ahora necesito unos datos para completar tu pedido:\n"
#                        "1) ¿Cuál es tu nombre?\n"
#                        "2) ¿Cuál es tu número de teléfono?\n"
#                        "3) ¿Será para recoger (pickup) o entrega a domicilio?\n"
#                        "4) Si es entrega: ¿Cuál es la dirección?\n"
#                        "5) Si es pickup: ¿En cuántos minutos pasarías a recoger?\n"
#                        "6) ¿Cuál es tu método de pago (efectivo, tarjeta u online)?") if lang == "es" else (
#                     "I now need a few details to complete your order:\n"
#                     "1) What's your name?\n"
#                     "2) What's your phone number?\n"
#                     "3) Pickup or delivery?\n"
#                     "4) If delivery: what's the address?\n"
#                     "5) If pickup: in how many minutes would you pick up?\n"
#                     "6) What is your payment method (cash, card, online)?")
#                 ss.conv.append({"role": "assistant", "content": pre})
#                 ss.collecting_info = True
#                 ss.next_field_idx = 0

#             # Si estamos en fase de datos, pregunta secuencial del siguiente campo que falte
#             if ss.collecting_info:
#                 missing_seq = ensure_all_required_present(
#                     ss.client_info, lang)
#                 if missing_seq:
#                     def next_question(field: str) -> str:
#                         if lang == "es":
#                             return {
#                                 "name": "¿Cuál es tu nombre?",
#                                 "phone": "¿Cuál es tu número de teléfono?",
#                                 "delivery_type": "¿Será para recoger (pickup) o entrega a domicilio?",
#                                 "address": "¿Cuál es la dirección para la entrega?",
#                                 "pickup_eta_min": "¿En cuántos minutos pasarías a recoger?",
#                                 "payment_method": "¿Cuál es tu método de pago (efectivo, tarjeta u online)?",
#                             }[field]
#                         else:
#                             return {
#                                 "name": "What is your name?",
#                                 "phone": "What is your phone number?",
#                                 "delivery_type": "Pickup or delivery?",
#                                 "address": "What is the delivery address?",
#                                 "pickup_eta_min": "In how many minutes would you pick up?",
#                                 "payment_method": "What is your payment method (cash, card, online)?",
#                             }[field]
#                     next_field = missing_seq[0]
#                     ss.conv.append(
#                         {"role": "assistant", "content": next_question(next_field)})
#                     # si no faltan, ya no añadimos nada aquí (el botón quedará habilitado)

#             # else:
#             #     # Ya tenemos todo → podemos confirmar
#             #     pass

#             st.rerun()

#         # Confirmar pedido
#         if confirm_clicked and not confirm_disabled:
#             order = create_order_from_chat_ready(
#                 client=ss.get("client_info", {}),
#                 items=ss.get("order_items", []),
#                 currency=currency,
#             )
#             ss.conv.append({"role": "assistant", "content": t(
#                 "¡Pedido listo! Gracias. Lo estamos preparando 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
#                 "Order confirmed! We're on it 🚗💨 for delivery, or ready at your pickup time."
#             )})
#             st.success(t("¡Pedido confirmado!", "Order confirmed!"))
#             st.rerun()

#         st.markdown('</div>', unsafe_allow_html=True)

#     # (Se eliminó el bloque inferior que duplicaba el botón Confirmar)


# if __name__ == "__main__":
#     main()

# -*- coding: utf-8 -*-
from __future__ import annotations
import re
import streamlit as st
from uuid import uuid4
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np

from backend.utils import render_js_carousel, menu_table_component
from backend.config import get_config
from backend.db import fetch_menu, fetch_menu_images, create_order_from_chat_ready
from backend.llm_chat import (
    client_assistant_reply,
    extract_client_info,
    ensure_all_required_present,
    parse_items_from_chat,
    client_voice_to_text
)

# ──────────────────────────────────────────────────────────────────────────────
# Config / estilos
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

st.markdown("""
<style>
.chat-box {
  border: 1px solid #eee; border-radius: 12px;
  padding: 10px 12px; height: 52vh; overflow-y: auto;
  background: #fafafa; display: flex; flex-direction: column; gap: 6px;
}
.msg-row { display: flex; align-items: flex-end; margin-bottom: 6px; }
.msg-row.right { justify-content: flex-end; }
.msg-row.left { justify-content: flex-start; }
.bubble {
  padding: 10px 12px; border-radius: 14px; max-width: 80%; font-size: 0.95rem;
  word-wrap: break-word; white-space: pre-wrap;
}
.bubble.user {
  background: #DCF8C6; color: #222; border-top-right-radius: 4px;
}
.bubble.bot {
  background: #E8F0FE; color: #222; border-top-left-radius: 4px;
}
.header-chip {
  font-weight: bold; font-size: 0.8rem; margin-bottom: 3px; opacity: 0.7;
}
.avatar {
  width: 28px; height: 28px; border-radius: 50%; margin: 0 5px;
  background: #ddd; display: flex; align-items: center; justify-content: center;
}
.avatar-bot { background: #E8F0FE; }
.avatar-user { background: #DCF8C6; }
.input-row { position: sticky; bottom: 0; background: #fff; padding-top: 8px; }
@media (max-width: 768px){
  .chat-box { height: 56vh; }
}
</style>
""", unsafe_allow_html=True)


def _t(lang: str):
    return (lambda es, en: es if lang == "es" else en)


# --- util: señales de cierre / extras / totales ---
CLOSE_SIGNALS_ES = [
    "eso sería todo", "eso es todo", "nada más", "no gracias", "listo",
    "está bien", "confirmar", "confirmo", "sería todo", "es todo"
]
CLOSE_SIGNALS_EN = [
    "that's all", "nothing else", "no thanks", "done",
    "ok that's it", "confirm", "that would be all"
]
EXTRA_PROMPTS_ES = [
    "¿algo más", "algo más", "deseas algo más", "quieres agregar",
    "¿alguna bebida", "¿algún postre", "te ofrezco", "¿te gustaría añadir"
]
EXTRA_PROMPTS_EN = [
    "anything else", "something else", "would you like to add",
    "any drink", "any dessert", "offer you", "add anything"
]


def contains_any(text: str, needles: list[str]) -> bool:
    low = (text or "").lower()
    return any(n in low for n in needles)


def adjust_total_wording(text: str, lang: str) -> tuple[str, bool]:
    """
    Si el asistente sugiere extras y al mismo tiempo dice 'total',
    lo cambiamos a 'subtotal' para no disparar la fase de datos todavía.
    Devuelve (texto_ajustado, se_cambiaron_totales).
    """
    low = (text or "").lower()
    is_spanish = (lang == "es")
    asks_extras = contains_any(
        low, EXTRA_PROMPTS_ES if is_spanish else EXTRA_PROMPTS_EN)

    if not asks_extras:
        return text, False

    # Solo si menciona 'total' (evitar tocar si ya dice 'subtotal')
    if "total" in low and "subtotal" not in low:
        # Reemplazo case-insensitive de 'total' por 'subtotal'
        adjusted = re.sub(r"(?i)\btotal\b", "subtotal", text)
        return adjusted, True

    return text, False


def looks_like_total_trigger(text: str) -> bool:
    """Dispara fase de datos solo cuando hay un 'TOTAL' explícito (no 'subtotal')."""
    low = (text or "").lower()
    money_tokens = ["total", "precio", "price", "$",
                    "usd", "eur", "s/.", "mxn", "cop", "ars"]
    if "subtotal" in low:
        return False
    return any(tok in low for tok in money_tokens)


def user_closed_intent(text: str, lang: str) -> bool:
    low = (text or "").lower()
    return contains_any(low, CLOSE_SIGNALS_ES if lang == "es" else CLOSE_SIGNALS_EN)


def next_question(field: str, lang: str) -> str:
    if lang == "es":
        return {
            "name": "¿Cuál es tu nombre?",
            "phone": "¿Cuál es tu número de teléfono?",
            "delivery_type": "¿Será para recoger (pickup) o entrega a domicilio?",
            "address": "¿Cuál es la dirección para la entrega?",
            "pickup_eta_min": "¿En cuántos minutos pasarías a recoger?",
            "payment_method": "¿Cuál es tu método de pago (efectivo, tarjeta u online)?",
        }[field]
    else:
        return {
            "name": "What is your name?",
            "phone": "What is your phone number?",
            "delivery_type": "Pickup or delivery?",
            "address": "What is the delivery address?",
            "pickup_eta_min": "In how many minutes would you pick up?",
            "payment_method": "What is your payment method (cash, card, online)?",
        }[field]

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
# def main():
#     cfg = get_config()
#     lang = cfg.get("language", "es")
#     t = _t(lang)
#     currency = cfg.get("currency", "USD")
#     assistant_name = cfg.get(
#         "assistant_name", "RAIVA" if lang == "es" else "RAIVA")

#     st.title(t("💬 Cliente", "💬 Client"))

#     # ── Menú
#     menu = fetch_menu()
#     if not menu:
#         st.warning(t("El restaurante aún no ha cargado su menú.",
#                      "The restaurant has not uploaded its menu yet."))
#         return

#     # ── Estado
#     ss = st.session_state
#     if "conv_id" not in ss:
#         ss.conv_id = uuid4().hex
#     if "conv" not in ss:
#         ss.conv = [{
#             "role": "assistant",
#             "content": t("Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
#                          "Thanks for contacting us. How can we help?")
#         }]
#     if "client_info" not in ss:
#         ss.client_info = {}
#     if "order_items" not in ss:
#         ss.order_items = []
#     if "pending_user_input" not in ss:
#         ss.pending_user_input = ""
#     if "collecting_info" not in ss:
#         ss.collecting_info = False
#     if "next_field_idx" not in ss:
#         ss.next_field_idx = 0

#     # ── Vista: tabla o imágenes
#     view = st.radio(
#         t("Visualización del menú", "Menu view"),
#         [t("Tabla", "Table"), t("Imágenes", "Images")],
#         horizontal=True
#     )

#     col_menu, col_chat = st.columns([1, 1])

#     # ── Menú (izquierda)
#     with col_menu:
#         st.subheader(t("📖 Menú", "📖 Menu"))
#         if view == t("Tabla", "Table"):
#             menu_table_component(menu, lang)
#         else:
#             gallery = fetch_menu_images()
#             if not gallery:
#                 st.info(t("No hay imágenes cargadas aún.",
#                           "No images uploaded yet."))
#             else:
#                 render_js_carousel(
#                     gallery, interval_ms=5000, aspect_ratio=16/7,
#                     key_prefix="client_menu", show_dots=True, height_px=520
#                 )

#     # ── Chat (derecha)
#     with col_chat:
#         # st.markdown('<div class="chat-box" id="chatBox">',
#         #             unsafe_allow_html=True)
#         for m in ss.conv:
#             if m["role"] == "user":
#                 st.markdown(
#                     f"""
#                     <div class="msg-row right">
#                       <div class="bubble user">
#                         <div class="header-chip">🙂 {t("Cliente", "Customer")}</div>{m["content"]}
#                       </div>
#                     </div>
#                     """,
#                     unsafe_allow_html=True
#                 )
#             else:
#                 st.markdown(
#                     f"""
#                     <div class="msg-row left">
#                       <div class="bubble bot">
#                         <div class="header-chip">{assistant_name}</div>{m["content"]}
#                       </div>
#                     </div>
#                     """,
#                     unsafe_allow_html=True
#                 )
#         # Scroll automático al final
#         st.markdown("""
#         <script>
#           const box = parent.document.querySelector('#chatBox');
#           if (box) { box.scrollTop = box.scrollHeight; }
#         </script>
#         """, unsafe_allow_html=True)
#         st.markdown('</div>', unsafe_allow_html=True)

#         # ── WebRTC (audio)
#         rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
#         media_constraints = {"audio": True, "video": False}
#         webrtc_ctx = webrtc_streamer(
#             key="client-ptt",
#             mode=WebRtcMode.SENDONLY,
#             rtc_configuration=rtc_cfg,
#             media_stream_constraints=media_constraints,
#             audio_receiver_size=256,
#             async_processing=True,
#         )

#         if "audio_buffer" not in ss:
#             ss.audio_buffer = []

#         class AudioProcessor:
#             def recv(self, frame: av.AudioFrame):
#                 pcm = frame.to_ndarray()
#                 ss.audio_buffer.append(pcm)
#                 if len(ss.audio_buffer) > 200:
#                     ss.audio_buffer = ss.audio_buffer[-200:]
#                 return frame

#         if webrtc_ctx and webrtc_ctx.state.playing:
#             webrtc_ctx.audio_processor = AudioProcessor()

#         # ── Input inferior: texto | Enviar | Confirmar | 🎙️
#         st.markdown('<div class="input-row">', unsafe_allow_html=True)
#         c1, c2, c3, c4 = st.columns([7, 1.5, 2, 1.5])

#         user_text = c1.text_input(
#             "message",
#             value=ss.get("pending_user_input", ""),
#             key="client_input",
#             placeholder=t("Escribe tu mensaje…", "Type your message…"),
#             label_visibility="collapsed"
#         )
#         send_clicked = c2.button(t("Enviar", "Send"), use_container_width=True)

#         missing = ensure_all_required_present(ss.get("client_info", {}), lang)
#         confirm_disabled = bool(missing)
#         confirm_clicked = c3.button(
#             t("Confirmar", "Confirm"),
#             use_container_width=True,
#             disabled=confirm_disabled
#         )
#         mic_clicked = c4.button("🎙️", use_container_width=True)

#         # ── Mic → transcribir
#         if mic_clicked and ss.audio_buffer:
#             wav_bytes = np.concatenate(ss.audio_buffer, axis=1).tobytes()
#             ss.audio_buffer = []
#             text = client_voice_to_text(wav_bytes, cfg)
#             if text:
#                 cur = ss.get("pending_user_input", "")
#                 ss.pending_user_input = (cur + " " + text).strip()
#                 st.rerun()

#         # ── Enviar mensaje al LLM
#         if send_clicked and user_text.strip():
#             ss.conv.append({"role": "user", "content": user_text.strip()})
#             ss.pending_user_input = ""

#             reply = client_assistant_reply(
#                 ss.conv, menu, cfg, conversation_id=ss.conv_id
#             )
#             ss.conv.append({"role": "assistant", "content": reply})

#             # Extraer info
#             info = extract_client_info(ss.conv, lang)
#             ss.client_info.update({k: v for k, v in info.items() if v})
#             ss.order_items = parse_items_from_chat(ss.conv, menu, cfg)

#             # ── Trigger inteligente para pedir datos del cliente
#             def _looks_like_total_or_close(reply_text: str, user_text: str) -> bool:
#                 r = (reply_text or "").lower()
#                 u = (user_text or "").lower()
#                 money_signals = ["total", "subtotal", "precio", "price",
#                                  "$", "usd", "eur", "s/.", "mxn", "cop", "ars"]
#                 close_signals = ["eso sería todo", "listo", "confirmar", "confirmo",
#                                  "that's all", "done", "ok that's it", "confirm"]
#                 return any(s in r for s in money_signals) or any(s in u for s in close_signals)

#             last_assistant = next(
#                 (m["content"] for m in reversed(ss.conv) if m["role"] == "assistant"), "")
#             should_collect = ss.order_items and _looks_like_total_or_close(
#                 last_assistant, user_text)

#             if should_collect and not ss.collecting_info:
#                 pre = ("Ahora necesito unos datos para completar tu pedido:\n"
#                        "1) ¿Cuál es tu nombre?\n"
#                        "2) ¿Cuál es tu número de teléfono?\n"
#                        "3) ¿Será para recoger (pickup) o entrega a domicilio?\n"
#                        "4) Si es entrega: ¿Cuál es la dirección?\n"
#                        "5) Si es pickup: ¿En cuántos minutos pasarías a recoger?\n"
#                        "6) ¿Cuál es tu método de pago (efectivo, tarjeta u online)?") if lang == "es" else (
#                     "I now need a few details to complete your order:\n"
#                     "1) What's your name?\n"
#                     "2) What's your phone number?\n"
#                     "3) Pickup or delivery?\n"
#                     "4) If delivery: what's the address?\n"
#                     "5) If pickup: in how many minutes would you pick up?\n"
#                     "6) What is your payment method (cash, card, online)?")
#                 ss.conv.append({"role": "assistant", "content": pre})
#                 ss.collecting_info = True
#                 ss.next_field_idx = 0

#             if ss.collecting_info:
#                 missing_seq = ensure_all_required_present(ss.client_info, lang)
#                 if missing_seq:
#                     def next_question(field: str) -> str:
#                         q_es = {
#                             "name": "¿Cuál es tu nombre?",
#                             "phone": "¿Cuál es tu número de teléfono?",
#                             "delivery_type": "¿Será para recoger (pickup) o entrega a domicilio?",
#                             "address": "¿Cuál es la dirección para la entrega?",
#                             "pickup_eta_min": "¿En cuántos minutos pasarías a recoger?",
#                             "payment_method": "¿Cuál es tu método de pago (efectivo, tarjeta u online)?",
#                         }
#                         q_en = {
#                             "name": "What is your name?",
#                             "phone": "What is your phone number?",
#                             "delivery_type": "Pickup or delivery?",
#                             "address": "What is the delivery address?",
#                             "pickup_eta_min": "In how many minutes would you pick up?",
#                             "payment_method": "What is your payment method (cash, card, online)?",
#                         }
#                         return q_es[field] if lang == "es" else q_en[field]
#                     next_field = missing_seq[0]
#                     ss.conv.append(
#                         {"role": "assistant",
#                             "content": next_question(next_field)}
#                     )
#                 else:
#                     ss.collecting_info = False

#             st.rerun()

#         # ── Confirmar pedido
#         if confirm_clicked and not confirm_disabled:
#             order = create_order_from_chat_ready(
#                 client=ss.get("client_info", {}),
#                 items=ss.get("order_items", []),
#                 currency=currency,
#             )
#             ss.conv.append({"role": "assistant", "content": t(
#                 "¡Pedido listo! Gracias. Lo estamos preparando 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
#                 "Order confirmed! We're on it 🚗💨 for delivery, or ready at your pickup time."
#             )})
#             st.success(t("¡Pedido confirmado!", "Order confirmed!"))
#             st.rerun()

#         st.markdown('</div>', unsafe_allow_html=True)


def main():
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)
    currency = cfg.get("currency", "USD")
    assistant_name = cfg.get("assistant_name", "RAIVA")

    st.title(t("💬 Cliente", "💬 Client"))

    # Botón de nuevo chat
    with st.sidebar:
        if st.button(t("🆕 Nuevo chat", "🆕 New chat"), use_container_width=True):
            for k in [
                "conv_id", "conv", "client_info", "order_items", "collecting_info",
                "last_question_field", "audio_buffer", "awaiting_done_before_total",
                "prompted_confirm"
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.experimental_rerun()

    # Menú
    menu = fetch_menu()
    if not menu:
        st.warning(t("El restaurante aún no ha cargado su menú.",
                     "The restaurant has not uploaded its menu yet."))
        return

    # Estado
    ss = st.session_state
    if "conv_id" not in ss:
        ss.conv_id = uuid4().hex
    if "conv" not in ss:
        ss.conv = [{
            "role": "assistant",
            "content": t(
                "Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
                "Thanks for contacting us. How can we help?"
            )
        }]
    if "client_info" not in ss:
        ss.client_info = {}
    if "order_items" not in ss:
        ss.order_items = []
    if "collecting_info" not in ss:
        ss.collecting_info = False
    if "last_question_field" not in ss:
        ss.last_question_field = None
    if "audio_buffer" not in ss:
        ss.audio_buffer = []
    if "awaiting_done_before_total" not in ss:
        ss.awaiting_done_before_total = False
    if "prompted_confirm" not in ss:
        ss.prompted_confirm = False  # para no repetir el mensaje "Pulsa Confirmar"

    # Vista: tabla o imágenes
    view = st.radio(
        t("Visualización del menú", "Menu view"),
        [t("Tabla", "Table"), t("Imágenes", "Images")],
        horizontal=True
    )

    col_menu, col_chat = st.columns([1, 1])

    # ── Menú (izquierda)
    with col_menu:
        st.subheader(t("📖 Menú", "📖 Menu"))
        if view == t("Tabla", "Table"):
            menu_table_component(menu, lang)
        else:
            gallery = fetch_menu_images()
            if not gallery:
                st.info(t("No hay imágenes cargadas aún.",
                        "No images uploaded yet."))
            else:
                # Si tu helper acepta height_px, mantenlo. Si no, elimínalo.
                render_js_carousel(
                    gallery, interval_ms=5000, aspect_ratio=16/7,
                    key_prefix="client_menu", show_dots=True, height_px=520
                )

    # ── Chat (derecha)
    with col_chat:
        for m in ss.conv:
            if m["role"] == "user":
                st.markdown(
                    f"""
                    <div class="msg-row right">
                      <div class="bubble user">
                        <div class="header-chip">🙂 {t("Cliente", "Customer")}</div>{m["content"]}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="msg-row left">
                      <div class="bubble bot">
                        <div class="header-chip">{assistant_name}</div>{m["content"]}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # WebRTC (audio)
        rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        media_constraints = {"audio": True, "video": False}
        webrtc_ctx = webrtc_streamer(
            key="client-ptt",
            mode=WebRtcMode.SENDONLY,
            rtc_configuration=rtc_cfg,
            media_stream_constraints=media_constraints,
            audio_receiver_size=256,
            async_processing=True,
        )

        class AudioProcessor:
            def recv(self, frame: av.AudioFrame):
                pcm = frame.to_ndarray()
                ss.audio_buffer.append(pcm)
                if len(ss.audio_buffer) > 200:
                    ss.audio_buffer = ss.audio_buffer[-200:]
                return frame

        if webrtc_ctx and webrtc_ctx.state.playing:
            webrtc_ctx.audio_processor = AudioProcessor()

        # Input inferior (Enter para enviar + limpia input)
        st.markdown('<div class="input-row">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([6, 1.3, 2, 1])

        with c1.form(key="send_form", clear_on_submit=True):
            user_text = st.text_input(
                "message",
                key="client_input",
                placeholder=t("Escribe tu mensaje…", "Type your message…"),
                label_visibility="collapsed",
            )
            send_clicked = st.form_submit_button(t("Enviar", "Send"))

        # Confirmar habilitado solo si no falta nada
        missing = ensure_all_required_present(ss.get("client_info", {}), lang)
        confirm_disabled = bool(missing)
        confirm_clicked = c3.button(t("Confirmar", "Confirm"),
                                    use_container_width=True,
                                    disabled=confirm_disabled)
        mic_clicked = c4.button("🎙️", use_container_width=True)

        # Mic → transcribir y procesar
        if mic_clicked and ss.audio_buffer:
            wav_bytes = np.concatenate(ss.audio_buffer, axis=1).tobytes()
            ss.audio_buffer = []
            text = client_voice_to_text(wav_bytes, cfg)
            if text:
                # enviar como si fuera texto
                user_text = text
                send_clicked = True

        # ── Enviar mensaje al LLM
        if send_clicked and (user_text or "").strip():
            ut = user_text.strip()

            # 1) Mapear respuestas a la última pregunta (sin obligar frases rígidas)
            last_q = ss.last_question_field

            def looks_like_name(txt: str) -> bool:
                if any(ch.isdigit() for ch in txt):
                    return False
                words = [w for w in txt.split() if w.isalpha()]
                return 1 <= len(words) <= 4 and len(txt) <= 60

            def normalize_phone(txt: str):
                digits = "".join(ch for ch in txt if ch.isdigit())
                return digits if len(digits) >= 7 else None

            mapped = False
            if ss.get("collecting_info"):
                if last_q == "name" and looks_like_name(ut):
                    ss.client_info["name"] = ut
                    mapped = True
                elif last_q == "phone":
                    ph = normalize_phone(ut)
                    if ph:
                        ss.client_info["phone"] = ph
                        mapped = True
                elif last_q == "delivery_type":
                    low = ut.lower()
                    if "pick" in low or "recog" in low:
                        ss.client_info["delivery_type"] = "pickup"
                        mapped = True
                    elif "deliver" in low or "domicil" in low or "env" in low:
                        ss.client_info["delivery_type"] = "delivery"
                        mapped = True
                elif last_q == "address":
                    if len(ut) >= 5:
                        ss.client_info["address"] = ut
                        mapped = True
                elif last_q == "pickup_eta_min":
                    m = re.search(r"(\d+)", ut)
                    if m:
                        ss.client_info["pickup_eta_min"] = int(m.group(1))
                        mapped = True
                elif last_q == "payment_method":
                    low = ut.lower()
                    if any(k in low for k in ["efectiv", "cash"]):
                        ss.client_info["payment_method"] = "cash"
                        mapped = True
                    elif any(k in low for k in ["tarjeta", "card", "débito", "credito", "crédito"]):
                        ss.client_info["payment_method"] = "card"
                        mapped = True
                    elif any(k in low for k in ["online", "transfer", "link"]):
                        ss.client_info["payment_method"] = "online"
                        mapped = True

            # 2) Añadir el mensaje del usuario al hilo
            ss.conv.append({"role": "user", "content": ut})

            # 3) Si aún no mapeamos, pedimos al LLM
            if not mapped:
                reply_raw = client_assistant_reply(
                    ss.conv, menu, cfg, conversation_id=ss.conv_id
                )
                # Cambiar 'total' -> 'subtotal' si el LLM aún ofrece extras:
                reply, downgraded = adjust_total_wording(reply_raw, lang)
                if downgraded:
                    ss.awaiting_done_before_total = True
                ss.conv.append({"role": "assistant", "content": reply})

                # Extraer info y items
                info = extract_client_info(ss.conv, lang)
                ss.client_info.update({k: v for k, v in info.items() if v})
                ss.order_items = parse_items_from_chat(ss.conv, menu, cfg)
            else:
                # Aun así extrae por si el texto incluía datos útiles
                info = extract_client_info(ss.conv, lang)
                ss.client_info.update({k: v for k, v in info.items() if v})

            # 4) Si el usuario dice que ya no quiere nada más y estábamos esperando,
            #    pedimos TOTAL final y arrancamos datos.
            if ss.awaiting_done_before_total and user_closed_intent(ut, lang):
                sys_hint = (
                    "El cliente ya no quiere agregar nada más. "
                    "Repite el TOTAL final (no subtotal) sin ofrecer extras, "
                    "y luego solicita los datos para confirmar."
                    if lang == "es" else
                    "The customer doesn't want to add anything else. "
                    "State the FINAL TOTAL (not subtotal) without upselling, "
                    "then ask for the details to confirm."
                )
                temp_history = ss.conv + \
                    [{"role": "system", "content": sys_hint}]
                reply2 = client_assistant_reply(
                    temp_history, menu, cfg, conversation_id=ss.conv_id
                )
                ss.conv.append({"role": "assistant", "content": reply2})
                ss.awaiting_done_before_total = False

            # 5) Disparar comienzo de fase de datos SOLO si hay TOTAL real o cierre claro
            last_assistant = next((m["content"] for m in reversed(
                ss.conv) if m["role"] == "assistant"), "")
            should_collect = (
                ss.order_items and
                (looks_like_total_trigger(last_assistant) or user_closed_intent(ut, lang)) and
                not ss.awaiting_done_before_total
            )
            if should_collect and not ss.collecting_info:
                pre = (
                    "Ahora necesito unos datos para completar tu pedido. Te los pediré uno a uno"
                    # "1) ¿Cuál es tu nombre?\n"
                    # "2) ¿Cuál es tu número de teléfono?\n"
                    # "3) ¿Será para recoger (pickup) o entrega a domicilio?\n"
                    # "4) Si es entrega: ¿Cuál es la dirección?\n"
                    # "5) Si es pickup: ¿En cuántos minutos pasarías a recoger?\n"
                    # "6) ¿Cuál es tu método de pago (efectivo, tarjeta u online)?"
                    if lang == "es" else
                    "I now need a few details to complete your order. I'll ask for them one by one"
                    # "1) What's your name?\n"
                    # "2) What's your phone number?\n"
                    # "3) Pickup or delivery?\n"
                    # "4) If delivery: what's the address?\n"
                    # "5) If pickup: in how many minutes would you pick up?\n"
                    # "6) What is your payment method (cash, card, online)?"
                )
                ss.conv.append({"role": "assistant", "content": pre})
                ss.collecting_info = True
                ss.last_question_field = None

            # 6) Si estamos en fase de datos, preguntar secuencialmente lo que falte
            if ss.collecting_info:
                missing_seq = ensure_all_required_present(ss.client_info, lang)
                if missing_seq:
                    nf = missing_seq[0]
                    ss.conv.append(
                        {"role": "assistant", "content": next_question(nf, lang)})
                    ss.last_question_field = nf
                else:
                    ss.last_question_field = None
                    ss.collecting_info = False
                    # Aviso explícito para que pulse Confirmar (solo una vez)
                    if not ss.prompted_confirm:
                        msg = (
                            "Pedido listo para confirmación. Por favor, presiona el botón **Confirmar**."
                            if lang == "es" else
                            "Order ready for confirmation. Please press the **Confirm** button."
                        )
                        ss.conv.append({"role": "assistant", "content": msg})
                        ss.prompted_confirm = True

            st.rerun()

        # Confirmar pedido
        if confirm_clicked and not confirm_disabled:
            create_order_from_chat_ready(
                client=ss.get("client_info", {}),
                items=ss.get("order_items", []),
                currency=currency,
            )
            ss.conv.append({"role": "assistant", "content": t(
                "¡Pedido listo! Gracias. Lo estamos preparando 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
                "Order confirmed! We're on it 🚗💨 for delivery, or ready at your pickup time."
            )})
            st.success(t("¡Pedido confirmado!", "Order confirmed!"))
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

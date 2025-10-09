# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

# # Basic i18n helper
# from __future__ import annotations

# STRINGS = {
#     "es": {
#         "app_title": "Asistente de Pedidos para Restaurantes",
#         "role_client": "Cliente",
#         "role_admin": "Restaurante (Admin)",
#         "lang_label": "Idioma",
#         "menu_required": "Para empezar, el restaurante debe cargar al menos un ítem del menú.",
#         "upload_audio": "Subir audio (voz a texto)",
#         "type_message": "Escribe tu mensaje",
#         "send": "Enviar",
#         "new_chat": "Nuevo chat",
#         "orders_header": "Órdenes Confirmadas",
#         "pending_header": "Interacciones por confirmar (1 minuto)",
#         "menu_header": "Gestión de Menú",
#         "add_item": "Agregar Ítem",
#         "bulk_upload": "Carga Masiva (CSV/TXT)",
#         "ocr_upload": "Cargar Imagen para OCR",
#         "confirm": "Confirmar",
#         "deny": "Negar",
#         "logs_header": "Logs y Descargas",
#         "download_orders": "Descargar Órdenes (CSV)",
#         "download_convos": "Descargar Conversaciones Difíciles (CSV)",
#         "client_info": "Datos del cliente",
#         "payment_info": "Información de pago",
#         "pickup_delivery": "Retiro o Domicilio",
#         "delivery_address": "Dirección de entrega",
#         "pickup_eta": "Tiempo estimado de retiro (min)",
#         "standby_msg": "Necesito confirmar esto con el restaurante. Dame 1 minuto por favor...",
#         "auto_approved": "He confirmado tu solicitud. ¡Continuemos!",
#         "order_confirmed_eta": "¡Listo! Tu pedido estará listo en 30 minutos o según tu solicitud.",
#         "voice_disabled": "Voz a texto deshabilitado (configura tu API para habilitar).",
#         "menu_visible": "Menú disponible",
#         "price": "Precio",
#         "currency": "Moneda",
#         "description": "Descripción",
#         "name": "Nombre",
#         "tags": "Etiquetas",
#         "save": "Guardar",
#         "cancel": "Cancelar",
#     },
#     "en": {
#         "app_title": "Restaurant Ordering Assistant",
#         "role_client": "Client",
#         "role_admin": "Restaurant (Admin)",
#         "lang_label": "Language",
#         "menu_required": "To start, the restaurant must upload at least one menu item.",
#         "upload_audio": "Upload audio (voice to text)",
#         "type_message": "Type your message",
#         "send": "Send",
#         "new_chat": "New chat",
#         "orders_header": "Confirmed Orders",
#         "pending_header": "Pending Confirmations (1 minute)",
#         "menu_header": "Menu Management",
#         "add_item": "Add Item",
#         "bulk_upload": "Bulk Upload (CSV/TXT)",
#         "ocr_upload": "Upload Image for OCR",
#         "confirm": "Approve",
#         "deny": "Deny",
#         "logs_header": "Logs & Downloads",
#         "download_orders": "Download Orders (CSV)",
#         "download_convos": "Download Difficult Conversations (CSV)",
#         "client_info": "Client info",
#         "payment_info": "Payment info",
#         "pickup_delivery": "Pickup or Delivery",
#         "delivery_address": "Delivery address",
#         "pickup_eta": "Pickup ETA (min)",
#         "standby_msg": "I need to confirm this with the restaurant. Give me 1 minute please...",
#         "auto_approved": "I’ve confirmed your request. Let’s continue!",
#         "order_confirmed_eta": "Done! Your order will be ready in 30 minutes or as requested.",
#         "voice_disabled": "Voice to text disabled (configure your API to enable).",
#         "menu_visible": "Available Menu",
#         "price": "Price",
#         "currency": "Currency",
#         "description": "Description",
#         "name": "Name",
#         "tags": "Tags",
#         "save": "Save",
#         "cancel": "Cancel",
#     },
# }


# def t(lang: str, key: str) -> str:
#     lang = (lang or "es").lower()
#     if lang not in STRINGS:
#         lang = "es"
#     return STRINGS[lang].get(key, key)

# backend/i18n.py
from __future__ import annotations

STRINGS = {
    "role_admin": {"es": "Restaurante (Admin)", "en": "Restaurant (Admin)"},
    "role_client": {"es": "Cliente", "en": "Client"},
}


def t(lang: str, key: str) -> str:
    lang = (lang or "es").lower()
    return STRINGS.get(key, {}).get(lang, key)

# 🍽️ Restaurant AI Demo — Conversational Ordering System

## 📋 Descripción

Este proyecto es un **demo funcional** de un sistema de pedidos para restaurantes impulsado por IA conversacional (basado en OpenAI GPT-4o-mini y LangChain).

Permite que:
- 👤 **Clientes** ordenen por chat (como WhatsApp) o voz.
- 🧑‍🍳 **Restaurantes** gestionen menús, pedidos, solicitudes difíciles y confirmaciones humanas.
- ⚙️ **Super Admins** configuren idioma, modelo, tono, y limpien datos o agreguen banners al menú.

---

## 🧩 Arquitectura

restaurant_demo_v3/
│
├── streamlit_app.py # Página principal de Streamlit (landing + idioma)
│
├── backend/
│ ├── db.py # SQLite + migraciones + lógica de menús, pedidos, banners
│ ├── faq.py # Base de conocimiento interna (FAQ)
│ ├── llm_chat.py # Lógica LLM + prompt inteligente + STT/Whisper
│ ├── config.py # Configuración persistente global (modelo, idioma, tono)
│ ├── utils.py # Utilidades y renderización de tablas/galerías
│ └── ocr.py # OCR para leer menús desde imágenes
│
├── pages/
│ ├── 0_SuperAdmin.py # Configuración global + limpieza de datos + banners
│ ├── 1_Client.py # Interfaz tipo WhatsApp (chat o voz)
│ └── 2_Restaurante.py # Panel de restaurante (gestión de menú y pedidos)
│
├── hidden_pages/
│ └── 2_Admin.py # Versión anterior, mantenida pero no visible
│
├── data/ # Base SQLite y multimedia
│ ├── app.db
│ └── media/
│
└── .env # Contiene OPENAI_API_KEY

## 🚀 Características principales

### 💬 Cliente
- Chat bilingüe (Español / Inglés) estilo WhatsApp.
- Push-to-Talk con `streamlit-webrtc` (voz → texto en tiempo real).
- Menú en tabla o galería de imágenes.
- Detección automática de:  
  `nombre`, `teléfono`, `pickup/delivery`, `dirección`, `pago`, `tiempo estimado`.
- Validación dinámica antes de confirmar pedido.
- Banner superior del restaurante.

---

### 🧑‍🍳 Restaurante
- Carga de menú manual, masiva (CSV/TXT) u OCR desde imagen.  
  Formato estándar:

  | name | description | price | special_notes |
  |------|--------------|--------|----------------|
  | Pizza Margarita | Tomate, queso mozzarella, albahaca | 8.5 | vegetariano |
  | Hamburguesa BBQ | Carne, salsa BBQ, papas | 10.0 | alto en sal |

- Ordenes en cola: **confirmada → preparando → lista → entregada**.  
  Si pasa el SLA (30 min o ETA cliente), prioridad automática (flag roja).
- Chat humano para solicitudes difíciles (timeout 1 min → auto-approve + FAQ).
- Comandos de voz para cambiar estado de órdenes o aprobar solicitudes.

---

### ⚙️ Super Admin
- Configuración global:
  - Idioma (ES/EN)
  - Modelo (GPT-4o-mini por defecto)
  - Temperatura
  - Nombre y tono de la LLM
- Limpieza completa de base:
  - Conversaciones difíciles
  - Órdenes
  - Menús / Ítems / Imágenes / Banners
- Subida y vista de **banner** del restaurante.
- Acceso a pantallas ocultas para soporte.

---

### 🧠 FAQ Interna
Cada vez que el encargado aprueba una solicitud (o expira a 1 min),  
se registra en una tabla FAQ. Si otro cliente pregunta lo mismo,  
la IA responderá automáticamente sin requerir aprobación humana.

---

## 📱 Diseño responsive

- **Cliente:** optimizado para móviles (ancho ≤ 900 px).
- **Restaurante / Admin:** óptimo en desktop.
- Burbuja verde (cliente) / blanca (asistente).
- Auto-scroll del chat, scroll fijo en menú, y layout columnar adaptable.

---

## 🔧 Requisitos

- Python 3.12+
- Clave OpenAI en `.env`:
OPENAI_API_KEY=tu_clave_aqui

## 🪄 Instalación

```bash
python -m venv .venv
.venv\Scripts\activate     # Windows PowerShell
pip install --upgrade pip
pip install -r requirements.txt
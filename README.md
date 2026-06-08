# 🤖 Chatbot de Ventas con IA

Agente de inteligencia artificial para empresas que responde preguntas frecuentes y gestiona citas de forma autónoma. Construido con Flask, Claude (Anthropic) y conectado a Google Calendar y WhatsApp.

## ✨ Características

- **RAG (Retrieval-Augmented Generation):** el agente busca en los documentos de la empresa antes de responder, asegurando respuestas precisas y contextualizadas.
- **Gestión autónoma de citas:** cuando el cliente facilita todos los datos (nombre, teléfono, servicio, día y hora), el agente crea automáticamente un evento en Google Calendar y envía una confirmación por WhatsApp.
- **Detección de conflictos:** verifica disponibilidad en el calendario antes de confirmar; si el slot está ocupado, pide otro horario al cliente.
- **Tool use / Function calling:** el modelo decide cuándo ejecutar acciones reales en el mundo externo, no solo cuándo responder texto.
- **Multi-tenant:** una misma instancia sirve a varias empresas, cada una con sus propios documentos y calendario.
- **Doble canal:** widget web (`/chat`) y webhook de WhatsApp (`/whatsapp`).

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python · Flask · Flask-CORS |
| IA | Claude (Anthropic API) · Tool use |
| Calendario | Google Calendar API · OAuth 2.0 |
| Mensajería | Twilio WhatsApp |
| Recuperación | RAG con búsqueda TF-IDF sobre documentos `.txt` / `.md` |

## 📁 Estructura del proyecto

```
chatbot-ventas/
├── backend/
│   ├── server.py          # API Flask: endpoints /chat y /whatsapp
│   ├── citas.py           # Gestión de citas: Google Calendar + WhatsApp
│   ├── gcal.py            # Módulo Google Calendar (OAuth, eventos, conflictos)
│   ├── auth_gcal.py       # Script de autorización OAuth (ejecutar una vez)
│   ├── test_whatsapp.py   # Prueba de envío por WhatsApp
│   ├── test_gcal.py       # Prueba de integración con Google Calendar
│   ├── requirements.txt
│   └── .env.example       # Variables de entorno necesarias
├── widget/                # Burbuja de chat embebible en cualquier web
├── empresas/
│   └── demo/              # Documentos de la empresa (FAQs, manuales, etc.)
└── docs/
    └── GUIA.md            # Guía completa de instalación y despliegue
```

## 🚀 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/gonzaloum2001/chatbot-ventas.git
cd chatbot-ventas/backend

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus credenciales

# 4. Autorizar Google Calendar (solo la primera vez)
python auth_gcal.py

# 5. Arrancar el servidor
python server.py
```

## ⚙️ Variables de entorno

Copia `.env.example` a `.env` y rellena:

| Variable | Descripción |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key de Anthropic |
| `TWILIO_SID` | Account SID de Twilio |
| `TWILIO_TOKEN` | Auth Token de Twilio |
| `TWILIO_FROM` | Número WhatsApp Twilio (`whatsapp:+14155238886`) |
| `GCAL_TIMEZONE` | Zona horaria (ej. `Europe/Madrid`) |
| `GCAL_CALENDAR_ID` | ID del calendario (`primary` por defecto) |
| `EMPRESA` | Nombre de la carpeta de documentos en `empresas/` |

## 📖 Cómo funciona

1. El cliente escribe por el widget web o WhatsApp.
2. El servidor recupera los fragmentos más relevantes de los documentos de la empresa (RAG).
3. Claude genera una respuesta usando solo esa información.
4. Si el cliente quiere una cita, el agente recoge los datos necesarios de forma natural.
5. Al tener los 5 datos, llama a la herramienta `guardar_cita` → crea el evento en Google Calendar → envía confirmación por WhatsApp.
6. Si el slot está ocupado, informa al cliente y le pide otro horario.

## 📄 Licencia

MIT

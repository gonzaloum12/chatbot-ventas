# Chatbot para empresas — Guía completa

Un chatbot que responde **FAQs**, gestiona **reservas/citas** y da **soporte técnico**,
basándose en los documentos de cada empresa cliente. Funciona en **web** y en **WhatsApp**.

## Cómo funciona (en 1 minuto)

1. Por cada empresa cliente creas una carpeta en `empresas/` con sus documentos (FAQs, precios, manuales...).
2. El backend lee esos documentos, y cuando llega una pregunta busca los trozos relevantes y se los pasa a Claude para que responda **solo con esa información** (esto se llama RAG: no inventa).
3. El mismo backend atiende dos canales: el **widget web** (una burbuja de chat) y **WhatsApp**.

```
empresas/demo/*.md   →   backend/server.py   →   widget web  +  WhatsApp
   (conocimiento)          (Claude + RAG)          (canales)
```

---

# PARTE 1 — Probarlo en tu ordenador

### 1. Requisitos
- Python 3.10 o superior.
- Una clave de API de Anthropic: la sacas en https://console.anthropic.com (Settings → API Keys).

### 2. Instalar
```bash
cd backend
pip install -r requirements.txt
```

### 3. Poner tu clave
```bash
# Mac / Linux
export ANTHROPIC_API_KEY="sk-ant-tu-clave-aqui"

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-tu-clave-aqui"
```

### 4. Arrancar el backend
```bash
python server.py
```
Verás algo como: `Empresa: demo | Documentos: 3 trozos | Modelo: claude-haiku-4-5`.
El servidor queda escuchando en `http://localhost:5000`.

### 5. Probar el widget web
Abre el archivo `widget/prueba.html` en tu navegador (doble clic).
Aparece la burbuja 💬 abajo a la derecha. Pregúntale:
- «¿Qué horario tenéis?»
- «¿Cuánto cuesta un tinte?»
- «Quiero reservar para cortarme el pelo el sábado»

> Si el navegador bloquea la conexión por CORS, sirve la página con un mini servidor:
> `cd widget && python -m http.server 8000` y abre `http://localhost:8000/prueba.html`.

### 6. (Opcional) Probar WhatsApp sin tener WhatsApp
Sin token configurado, el backend "simula" el envío e imprime la respuesta en la terminal:
```bash
curl -X POST http://localhost:5000/whatsapp -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"34600111222","text":{"body":"¿Cuánto cuesta un corte?"}}]}}]}]}'
```
Mira la terminal del servidor: verás `[WhatsApp simulado] -> 34600111222: ...`.

---

# PARTE 2 — Montarlo para tus clientes

## Paso A — Crear el conocimiento de cada cliente
Crea una carpeta por empresa y mete sus documentos en `.md` o `.txt`:
```
empresas/
  peluqueria-estilo/   faqs.md  precios.md  reservas.md
  clinica-dental/      faqs.md  servicios.md
```
Arranca el backend apuntando a esa empresa:
```bash
EMPRESA=peluqueria-estilo python server.py
```
> Recomendación: **un proceso/servidor por cliente**. Así sus datos quedan aislados.

## Paso B — Subir el backend a internet
El backend es una app Flask normal. Opciones sencillas (de menos a más control):

| Servicio | Ideal para | Notas |
|----------|-----------|-------|
| **Render.com** / **Railway** | Empezar rápido | Conectas el repo, pones `ANTHROPIC_API_KEY` como variable y listo |
| **Fly.io** | Bajo coste y global | Despliegue con Docker |
| **VPS** (Hetzner, DigitalOcean) | Más control | Tú gestionas el servidor con gunicorn + nginx |

Para producción no uses `python server.py`; usa un servidor WSGI:
```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 server:app
```
Tu backend quedará en una URL tipo `https://chatbot-peluqueria.onrender.com`.

## Paso C — Instalarlo en la WEB del cliente
1. Sube `widget/widget.js` a tu servidor (o a un hosting estático/CDN).
2. El cliente pega **una sola línea** antes de `</body>` en su web:
```html
<script src="https://TU-SERVIDOR/widget.js"
        data-api="https://chatbot-peluqueria.onrender.com/chat"></script>
```
Funciona en cualquier web: WordPress, Shopify, Wix, HTML a mano, etc.
(En WordPress se pega en el editor de tema o con un plugin de "insertar código".)

## Paso D — Conectarlo a WHATSAPP
Dos caminos. **Twilio** es el más fácil para empezar; **Meta** es más barato a escala.

### Opción 1 — Twilio (recomendada para empezar)
1. Crea cuenta en twilio.com y activa el **WhatsApp Sandbox** (para pruebas) o pide un número propio.
2. En la configuración del número, pon como webhook entrante:
   `https://chatbot-peluqueria.onrender.com/whatsapp`
3. Twilio manda los mensajes a ese endpoint. (El formato de Twilio difiere un poco
   del de Meta; en `server.py` está comentado dónde adaptarlo — son 3 líneas.)

### Opción 2 — Meta WhatsApp Cloud API (oficial, barata a escala)
1. Crea una app en https://developers.facebook.com y añade el producto **WhatsApp**.
2. Configura el webhook apuntando a `https://tu-servidor/whatsapp` con un **token de verificación**.
   Pon ese mismo token en la variable `VERIFY_TOKEN`. El backend ya responde a la verificación (GET).
3. Copia el **token permanente** y el **Phone Number ID** a las variables:
   ```bash
   export WHATSAPP_TOKEN="..."
   export WHATSAPP_PHONE_ID="..."
   export VERIFY_TOKEN="el-que-pusiste-en-meta"
   ```
4. Para mensajes salientes fuera de la ventana de 24h, WhatsApp exige **plantillas aprobadas**.

> Importante: WhatsApp requiere que la empresa tenga un perfil de negocio verificado.
> Tú lo configuras, pero la cuenta debe ser del cliente.

---

# Variables de configuración (resumen)

| Variable | Para qué | Por defecto |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Tu clave de Claude | (obligatoria) |
| `EMPRESA` | Carpeta de la empresa cliente | `demo` |
| `MODEL` | Modelo de Claude | `claude-haiku-4-5` |
| `PORT` | Puerto del servidor | `5000` |
| `WHATSAPP_TOKEN` / `WHATSAPP_PHONE_ID` | WhatsApp (Meta) | — |
| `VERIFY_TOKEN` | Verificación webhook | `mi_token` |

**¿Qué modelo elegir?** `claude-haiku-4-5` es rápido y barato, perfecto para FAQs de alto
volumen. Si necesitas respuestas más razonadas (soporte técnico complejo), cambia a
`claude-opus-4-8`. Se cambia sin tocar el código: `MODEL=claude-opus-4-8 python server.py`.

---

# Cómo mejorar el chatbot (siguientes pasos)

- **Búsqueda más precisa:** ahora la búsqueda en documentos es por palabras. Para bases de
  conocimiento grandes, usa *embeddings* (vectores) con una base como Chroma o pgvector.
  Mejora mucho cuando el cliente pregunta con palabras distintas a las del documento.
- **Leer PDF/Word:** hoy lee `.md` y `.txt`. Añade conversión de PDF/DOCX a texto al cargar.
- **Reservas reales:** conecta el bot a Google Calendar o a la agenda del cliente para crear citas de verdad.
- **Guardar conversaciones:** ahora la memoria está en RAM (se borra al reiniciar). Usa Redis o una base de datos.
- **Pasar a un humano:** detecta cuándo el bot no sabe y avisa al equipo (email, Slack).

# Cómo venderlo (modelo de negocio)
- **Cuota mensual por cliente** (p. ej. 30–150 €/mes) según volumen de mensajes.
- **Pago único de instalación** por configurar su conocimiento y conectar sus canales.
- Tu coste principal es la API de Claude (céntimos por conversación con Haiku) + el hosting.

---

# PARTE 3 — Citas reales y confirmaciones (añadido)

Ahora el bot **guarda las citas** y **envía confirmación**. Cómo funciona:

- Cuando el bot reúne los 5 datos (nombre, teléfono, servicio, día, hora), llama por su
  cuenta a la herramienta `guardar_cita`. Esto NO es texto inventado: se ejecuta de verdad.
- La cita se guarda en `citas/<empresa>.json`.
- Acto seguido se envía la confirmación al teléfono del cliente.

### Probarlo en local (sin credenciales)
No necesitas nada: si no hay credenciales, la confirmación se "simula" y aparece en la
terminal del servidor como `[CONFIRMACIÓN SIMULADA]`. Así ves que el flujo entero funciona.
La cita sí se guarda de verdad en `citas/<empresa>.json`.

### Activar el envío REAL — Opción WhatsApp (Meta)
Pon estas variables antes de arrancar (las obtienes en developers.facebook.com):
```bash
export WHATSAPP_TOKEN="tu-token-permanente"
export WHATSAPP_PHONE_ID="tu-phone-number-id"
```
Recuerda: para mensajes que el negocio inicia fuera de la ventana de 24h, WhatsApp exige
**plantillas aprobadas** por Meta. La confirmación inmediata tras la conversación entra
dentro de la ventana, así que funciona como texto normal.

### Activar el envío REAL — Opción SMS (Twilio)
Más sencillo si no quieres lidiar con la aprobación de WhatsApp:
```bash
export TWILIO_SID="tu-account-sid"
export TWILIO_TOKEN="tu-auth-token"
export TWILIO_FROM="+1XXXXXXXXXX"   # tu número de Twilio
```

El bot usa WhatsApp si encuentra esas variables; si no, prueba SMS; si no, simula.

### Dónde se guardan las citas
En la carpeta `citas/`, un archivo JSON por empresa. Para verlas, abre el archivo.
Cuando quieras algo más serio (Google Calendar, una base de datos, un panel para verlas),
solo hay que cambiar el archivo `backend/citas.py`: el resto del bot no se entera.

### Resumen de variables nuevas
| Variable | Para qué |
|----------|----------|
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID` | Enviar confirmación por WhatsApp (Meta) |
| `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_FROM` | Enviar confirmación por SMS (Twilio) |

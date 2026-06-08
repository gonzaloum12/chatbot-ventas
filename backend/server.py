"""
Chatbot para empresas — Backend con RAG + citas reales (tool use)
Canales: widget web (/chat) y WhatsApp (/whatsapp).
Novedad: cuando el bot tiene todos los datos de una cita, llama a la
herramienta guardar_cita, que la registra y envía la confirmación.
"""
import os
import glob
import math
import re
from dotenv import load_dotenv
load_dotenv()  # carga las variables de backend/.env automáticamente
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from anthropic import Anthropic

import citas  # módulo nuevo: guardar y confirmar citas

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
MODEL = os.environ.get("MODEL", "claude-haiku-4-5")
EMPRESA = os.environ.get("EMPRESA", "demo")
DOCS_DIR = os.environ.get("DOCS_DIR",
    os.path.join(os.path.dirname(__file__), "..", "empresas", EMPRESA))

client = Anthropic()
app = Flask(__name__)
CORS(app)
SESIONES = {}

# ---------------------------------------------------------------------------
# RAG (igual que antes)
# ---------------------------------------------------------------------------
def trocear(texto, tam=600):
    palabras = texto.split()
    return [" ".join(palabras[i:i + tam]) for i in range(0, len(palabras), tam)]

def cargar_documentos():
    trozos = []
    for ruta in glob.glob(os.path.join(DOCS_DIR, "**", "*"), recursive=True):
        if ruta.endswith((".txt", ".md")):
            with open(ruta, encoding="utf-8") as f:
                for t in trocear(f.read()):
                    trozos.append({"fuente": os.path.basename(ruta), "texto": t})
    return trozos

BASE_CONOCIMIENTO = cargar_documentos()

def buscar(consulta, k=4):
    palabras_q = set(re.findall(r"\w+", consulta.lower()))
    puntuados = []
    for trozo in BASE_CONOCIMIENTO:
        palabras_t = set(re.findall(r"\w+", trozo["texto"].lower()))
        score = len(palabras_q & palabras_t) / (math.sqrt(len(palabras_t)) + 1)
        if score > 0:
            puntuados.append((score, trozo))
    puntuados.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in puntuados[:k]]

# ---------------------------------------------------------------------------
# Herramienta que Claude puede usar para registrar una cita
# ---------------------------------------------------------------------------
HERRAMIENTAS = [{
    "name": "guardar_cita",
    "description": (
        "Registra una cita o reserva CUANDO tengas TODOS los datos confirmados por el "
        "cliente. No la llames si falta algún dato; en su lugar, pregunta por lo que falte."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "nombre": {"type": "string", "description": "Nombre del cliente"},
            "telefono": {"type": "string", "description": "Teléfono internacional, ej. +34600111222"},
            "servicio": {"type": "string", "description": "Servicio solicitado"},
            "dia": {"type": "string", "description": "Día de la cita, ej. 2026-06-14 o 'sábado 14'"},
            "hora": {"type": "string", "description": "Hora de la cita, ej. 17:00"},
        },
        "required": ["nombre", "telefono", "servicio", "dia", "hora"],
    },
}]

INSTRUCCIONES = """Eres el asistente virtual de la empresa. Tu trabajo:
1. Responder preguntas frecuentes (FAQs) usando SOLO la información del contexto.
2. Gestionar reservas y citas: reúne nombre, teléfono, servicio, día y hora.
3. Dar soporte técnico básico siguiendo los manuales del contexto.

Reglas para CITAS:
- Pide los datos que falten, uno o dos a la vez, de forma natural.
- Cuando tengas los CINCO datos (nombre, teléfono, servicio, día, hora), confírmalos
  brevemente con el cliente y llama a la herramienta guardar_cita.
- No digas que la cita está confirmada hasta que la herramienta la haya registrado.

Reglas generales:
- Usa SOLO la información del CONTEXTO para datos del negocio. Si no está, dilo con
  honestidad y ofrece pasar con una persona del equipo.
- No inventes precios, horarios ni políticas. Responde breve y en el idioma del usuario."""

def responder(mensaje, sesion_id):
    historial = SESIONES.get(sesion_id, [])
    contexto = "\n\n".join(f"[{t['fuente']}]\n{t['texto']}" for t in buscar(mensaje)) \
        or "(sin documentos cargados)"
    historial.append({"role": "user", "content": mensaje})
    system = f"{INSTRUCCIONES}\n\n=== CONTEXTO ===\n{contexto}"

    while True:
        resp = client.messages.create(
            model=MODEL, max_tokens=1000, system=system,
            messages=historial, tools=HERRAMIENTAS,
        )
        historial.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "tool_use":
            resultados = []
            for bloque in resp.content:
                if bloque.type == "tool_use" and bloque.name == "guardar_cita":
                    datos = bloque.input
                    try:
                        cita = citas.guardar_cita(EMPRESA, **datos)
                        texto_conf = (
                            f"\u2705 Cita confirmada para {cita['nombre']}:\n"
                            f"{cita['servicio']} el {cita['dia']} a las {cita['hora']}.\n"
                            f"\u00a1Te esperamos!"
                        )
                        canal = citas.enviar_confirmacion(cita["telefono"], texto_conf)
                        resultado_texto = f"Cita guardada y confirmación enviada por {canal}."
                    except citas.CitaOcupadaError as e:
                        resultado_texto = f"ERROR_HORARIO_OCUPADO: {e}"
                    resultados.append({
                        "type": "tool_result", "tool_use_id": bloque.id,
                        "content": resultado_texto,
                    })
            historial.append({"role": "user", "content": resultados})
            continue

        texto = "".join(b.text for b in resp.content if b.type == "text")
        SESIONES[sesion_id] = historial[-20:]
        return texto

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    datos = request.get_json(force=True)
    mensaje = datos.get("mensaje", "")
    if not mensaje:
        return jsonify({"error": "Falta el mensaje"}), 400
    return jsonify({"respuesta": responder(mensaje, datos.get("sesion", "anon"))})

@app.route("/whatsapp", methods=["GET", "POST"])
def whatsapp():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == os.environ.get("VERIFY_TOKEN", "mi_token"):
            return Response(request.args.get("hub.challenge", ""), mimetype="text/plain")
        return "Token inválido", 403
    datos = request.get_json(force=True)
    try:
        entrada = datos["entry"][0]["changes"][0]["value"]["messages"][0]
        numero = entrada["from"]
        texto = entrada["text"]["body"]
        citas.enviar_confirmacion(numero, responder(texto, sesion_id=numero))
    except (KeyError, IndexError):
        pass
    return jsonify({"status": "ok"})

@app.route("/")
def home():
    return jsonify({"estado": "ok", "empresa": EMPRESA,
                    "documentos_cargados": len(BASE_CONOCIMIENTO)})

if __name__ == "__main__":
    print(f"Empresa: {EMPRESA} | Documentos: {len(BASE_CONOCIMIENTO)} trozos | Modelo: {MODEL}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

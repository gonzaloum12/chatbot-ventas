"""
Gestión de citas: guardado y confirmación.
Las citas se guardan en un archivo JSON por empresa Y en Google Calendar.
Cada cita ocupa exactamente 1 hora; si el slot ya está ocupado se lanza
CitaOcupadaError para que el bot pueda pedir otro horario al cliente.
"""
import os
import json
import datetime

CITAS_DIR = os.path.join(os.path.dirname(__file__), "..", "citas")
os.makedirs(CITAS_DIR, exist_ok=True)

# Google Calendar se activa sólo si existe credentials.json o token.json
_GCAL_DISPONIBLE = None  # se evalúa la primera vez que se necesita


class CitaOcupadaError(Exception):
    """Se lanza cuando el slot solicitado ya está ocupado en el calendario."""
    pass


def _gcal_activo():
    """Devuelve True si Google Calendar está configurado."""
    global _GCAL_DISPONIBLE
    if _GCAL_DISPONIBLE is None:
        base = os.path.dirname(__file__)
        tiene_creds = os.path.exists(os.path.join(base, "credentials.json"))
        tiene_token = os.path.exists(os.path.join(base, "token.json"))
        _GCAL_DISPONIBLE = tiene_creds or tiene_token
    return _GCAL_DISPONIBLE


def guardar_cita(empresa, nombre, telefono, servicio, dia, hora):
    """
    Guarda la cita en citas/<empresa>.json y, si Google Calendar está
    configurado, verifica disponibilidad y crea el evento (1 hora).

    Lanza CitaOcupadaError si el slot está ocupado en el calendario.
    Devuelve un dict con los datos de la cita (incluye google_event_id si aplica).
    """
    # --- 1. Verificar disponibilidad en Google Calendar ---
    google_event_id = None
    if _gcal_activo():
        try:
            import gcal
            if not gcal.verificar_disponibilidad(dia, hora):
                raise CitaOcupadaError(
                    f"El horario {hora} del {dia} ya está ocupado. "
                    "Por favor elige otro horario."
                )
            google_event_id = gcal.crear_evento({
                "nombre": nombre,
                "telefono": telefono,
                "servicio": servicio,
                "dia": dia,
                "hora": hora,
                "registrada": datetime.datetime.now().isoformat(timespec="seconds"),
            })
        except CitaOcupadaError:
            raise
        except Exception as e:
            # Si Google Calendar falla por razones técnicas, registramos el error
            # pero no bloqueamos la cita (degradación elegante)
            print(f"[GCAL WARNING] No se pudo sincronizar con Google Calendar: {e}")

    # --- 2. Guardar en JSON local ---
    ruta = os.path.join(CITAS_DIR, f"{empresa}.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            citas = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        citas = []

    cita = {
        "nombre": nombre,
        "telefono": telefono,
        "servicio": servicio,
        "dia": dia,
        "hora": hora,
        "registrada": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    if google_event_id:
        cita["google_event_id"] = google_event_id

    citas.append(cita)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(citas, f, ensure_ascii=False, indent=2)

    return cita


def enviar_confirmacion(telefono, texto):
    """Envía la confirmación por WhatsApp (Twilio sandbox o Meta) según config.
    Si no hay credenciales, lo simula imprimiéndolo (útil para pruebas)."""
    import requests

    tw_sid   = os.environ.get("TWILIO_SID")
    tw_token = os.environ.get("TWILIO_TOKEN")
    tw_from  = os.environ.get("TWILIO_FROM")  # debe incluir prefijo whatsapp:

    # --- Opción A: WhatsApp vía Twilio (sandbox o número aprobado) ---
    if tw_sid and tw_token and tw_from:
        # Asegurar prefijo whatsapp: en ambos números
        from_ = tw_from if tw_from.startswith("whatsapp:") else f"whatsapp:{tw_from}"
        to_   = telefono if telefono.startswith("whatsapp:") else f"whatsapp:{telefono}"
        r = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{tw_sid}/Messages.json",
            auth=(tw_sid, tw_token),
            data={"From": from_, "To": to_, "Body": texto},
            timeout=15,
        )
        print(f"[WHATSAPP] Estado: {r.status_code} | {r.json().get('status', r.text)}")
        return "whatsapp_twilio"

    # --- Opción B: WhatsApp Cloud API (Meta) ---
    wa_token    = os.environ.get("WHATSAPP_TOKEN")
    wa_phone_id = os.environ.get("WHATSAPP_PHONE_ID")
    if wa_token and wa_phone_id:
        requests.post(
            f"https://graph.facebook.com/v21.0/{wa_phone_id}/messages",
            headers={"Authorization": f"Bearer {wa_token}"},
            json={"messaging_product": "whatsapp", "to": telefono,
                  "type": "text", "text": {"body": texto}},
            timeout=15,
        )
        return "whatsapp_meta"

    # --- Sin credenciales: simulación para pruebas locales ---
    print(f"\n[CONFIRMACIÓN SIMULADA] -> {telefono}:\n{texto}\n")
    return "simulado"

"""
Integración con Google Calendar.
- Autenticación OAuth 2.0 (flujo local, token guardado en token.json).
- verificar_disponibilidad(dia, hora) → True si el slot de 1 h está libre.
- crear_evento(cita) → event_id del evento creado.
"""

import os
import datetime
import re
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = os.environ.get("GCAL_TIMEZONE", "Europe/Madrid")
CALENDAR_ID = os.environ.get("GCAL_CALENDAR_ID", "primary")
DURACION_HORAS = 1

# Rutas de credenciales (junto al propio módulo)
_BASE = os.path.dirname(__file__)
CREDENTIALS_FILE = os.path.join(_BASE, "credentials.json")
TOKEN_FILE = os.path.join(_BASE, "token.json")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def _get_service():
    """Devuelve un servicio autenticado de Google Calendar."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Falta {CREDENTIALS_FILE}. Descárgalo desde Google Cloud Console "
                    "(APIs & Services → Credentials → OAuth 2.0 Client IDs) y "
                    "ejecuta: python auth_gcal.py"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


# ---------------------------------------------------------------------------
# Parseo de fecha/hora
# ---------------------------------------------------------------------------
_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}
_DIAS_SEMANA = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
}


def parsear_datetime(dia: str, hora: str) -> datetime.datetime:
    """
    Combina dia y hora en un datetime con zona horaria.
    Acepta formatos como:
      - dia: "2026-06-14", "14/06/2026", "sábado 14", "14 de junio", "14 de junio de 2026"
      - hora: "17:00", "17h", "5pm"
    """
    tz = ZoneInfo(TIMEZONE)
    hoy = datetime.date.today()

    # --- Parsear hora ---
    hora = hora.strip().lower()
    hora_match = re.match(r"(\d{1,2})(?::(\d{2}))?(?:h|hs)?(?:\s*(am|pm))?", hora)
    if not hora_match:
        raise ValueError(f"Hora no reconocida: {hora!r}")
    h = int(hora_match.group(1))
    m = int(hora_match.group(2) or 0)
    if hora_match.group(3) == "pm" and h < 12:
        h += 12
    if hora_match.group(3) == "am" and h == 12:
        h = 0

    # --- Parsear día ---
    dia = dia.strip().lower()

    # ISO: 2026-06-14
    iso = re.match(r"(\d{4})-(\d{2})-(\d{2})", dia)
    if iso:
        fecha = datetime.date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        return datetime.datetime(fecha.year, fecha.month, fecha.day, h, m, tzinfo=tz)

    # dd/mm/yyyy o dd/mm
    slash = re.match(r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?", dia)
    if slash:
        anio = int(slash.group(3)) if slash.group(3) else hoy.year
        fecha = datetime.date(anio, int(slash.group(2)), int(slash.group(1)))
        return datetime.datetime(fecha.year, fecha.month, fecha.day, h, m, tzinfo=tz)

    # "14 de junio de 2026" / "14 de junio"
    texto_mes = re.match(r"(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{4}))?", dia)
    if texto_mes:
        mes_str = texto_mes.group(2)
        mes = _MESES.get(mes_str)
        if not mes:
            raise ValueError(f"Mes no reconocido: {mes_str!r}")
        anio = int(texto_mes.group(3)) if texto_mes.group(3) else hoy.year
        fecha = datetime.date(anio, mes, int(texto_mes.group(1)))
        return datetime.datetime(fecha.year, fecha.month, fecha.day, h, m, tzinfo=tz)

    # "sábado 14" → próximo sábado con día 14 (o siguiente mes si ya pasó)
    dia_sem_num_match = re.match(r"(\w+)\s+(\d{1,2})", dia)
    if dia_sem_num_match:
        nombre_dia = dia_sem_num_match.group(1)
        num_dia = int(dia_sem_num_match.group(2))
        if nombre_dia in _DIAS_SEMANA:
            # Buscar en los próximos 60 días el día con ese número
            for delta in range(0, 60):
                candidato = hoy + datetime.timedelta(days=delta)
                if candidato.day == num_dia:
                    return datetime.datetime(candidato.year, candidato.month, num_dia, h, m, tzinfo=tz)

    # Fallback: dateutil si está disponible
    try:
        from dateutil import parser as du_parser
        from dateutil.relativedelta import relativedelta  # noqa: F401
        dt = du_parser.parse(f"{dia} {hora}", dayfirst=True, default=datetime.datetime(hoy.year, hoy.month, hoy.day))
        return dt.replace(tzinfo=tz)
    except Exception:
        pass

    raise ValueError(f"No se pudo interpretar la fecha: dia={dia!r} hora={hora!r}")


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------
def verificar_disponibilidad(dia: str, hora: str) -> bool:
    """
    Devuelve True si el slot de DURACION_HORAS a partir de (dia, hora) está libre.
    Devuelve False si hay algún evento que se solape.
    """
    service = _get_service()
    inicio = parsear_datetime(dia, hora)
    fin = inicio + datetime.timedelta(hours=DURACION_HORAS)

    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=inicio.isoformat(),
        timeMax=fin.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return len(events.get("items", [])) == 0


def crear_evento(cita: dict) -> str:
    """
    Crea un evento de DURACION_HORAS en Google Calendar con los datos de la cita.
    Devuelve el event_id del evento creado.
    """
    service = _get_service()
    inicio = parsear_datetime(cita["dia"], cita["hora"])
    fin = inicio + datetime.timedelta(hours=DURACION_HORAS)

    evento = {
        "summary": f"{cita['servicio']} — {cita['nombre']}",
        "description": (
            f"Cliente: {cita['nombre']}\n"
            f"Teléfono: {cita['telefono']}\n"
            f"Servicio: {cita['servicio']}\n"
            f"Registrada: {cita.get('registrada', '')}"
        ),
        "start": {"dateTime": inicio.isoformat(), "timeZone": TIMEZONE},
        "end":   {"dateTime": fin.isoformat(),    "timeZone": TIMEZONE},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email",  "minutes": 60},
                {"method": "popup",  "minutes": 30},
            ],
        },
    }

    resultado = service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
    return resultado["id"]

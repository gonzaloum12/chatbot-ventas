"""
Prueba de envío de confirmación por WhatsApp vía Twilio sandbox.
Antes de correr este script:
  1. Ve a console.twilio.com → Messaging → Try it out → Send a WhatsApp message
  2. Envía el mensaje "join <palabra-palabra>" al número del sandbox desde tu WhatsApp
  3. Ejecuta: python test_whatsapp.py

    cd backend
    python test_whatsapp.py

Configura las variables en backend/.env antes de ejecutar.
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

SID   = os.environ["TWILIO_SID"]
TOKEN = os.environ["TWILIO_TOKEN"]
FROM  = os.environ["TWILIO_FROM"]  # ej: whatsapp:+14155238886
TO    = "whatsapp:+34654741735"    # cambia por el número de destino

print(f"Enviando WhatsApp de {FROM} a {TO}...")

r = requests.post(
    f"https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json",
    auth=(SID, TOKEN),
    data={
        "From": FROM,
        "To":   TO,
        "Body": "✅ Cita confirmada para Cliente Test:\nCorte de pelo el 2026-06-10 a las 17:00.\n¡Te esperamos!",
    },
    timeout=15,
)

data = r.json()
if r.status_code == 201:
    print(f"✅ Enviado. SID: {data['sid']}  |  Estado: {data['status']}")
else:
    print(f"❌ Error {r.status_code}: {data.get('message', data)}")

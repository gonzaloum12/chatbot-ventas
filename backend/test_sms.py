"""
Prueba directa de envío SMS con Twilio.
Ejecutar desde la carpeta backend/:  python test_sms.py

Configura las variables en backend/.env antes de ejecutar.
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

SID   = os.environ["TWILIO_SID"]
TOKEN = os.environ["TWILIO_TOKEN"]
FROM  = os.environ["TWILIO_FROM"].replace("whatsapp:", "")
TO    = "+34654741735"  # cambia por el número de destino

print(f"Enviando SMS de {FROM} a {TO}...")

r = requests.post(
    f"https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json",
    auth=(SID, TOKEN),
    data={"From": FROM, "To": TO,
          "Body": "✅ Prueba de SMS desde el chatbot de citas. ¡Funciona!"},
    timeout=15,
)

data = r.json()
if r.status_code == 201:
    print(f"✅ Aceptado. SID: {data['sid']}  |  Estado: {data['status']}")
    import time; time.sleep(5)
    r2 = requests.get(
        f"https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages/{data['sid']}.json",
        auth=(SID, TOKEN), timeout=15
    )
    d2 = r2.json()
    print(f"   Estado final: {d2['status']}  |  Error: {d2.get('error_message', 'ninguno')}")
else:
    print(f"❌ Error {r.status_code}: {data.get('message', data)}")

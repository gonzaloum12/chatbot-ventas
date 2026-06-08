"""
Ejecuta este script UNA SOLA VEZ desde la carpeta backend/ para autorizar
el acceso a Google Calendar y guardar el token.json.

    cd backend
    python auth_gcal.py

Se abrirá el navegador. Acepta los permisos con la cuenta de Google cuyo
calendario quieres usar. Después el script imprime "token.json guardado."
y puedes cerrar la ventana.
"""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE = os.path.dirname(__file__)
CREDENTIALS_FILE = os.path.join(BASE, "credentials.json")
TOKEN_FILE = os.path.join(BASE, "token.json")

if not os.path.exists(CREDENTIALS_FILE):
    print(
        "\n❌  No se encuentra credentials.json en la carpeta backend/.\n"
        "    Sigue los pasos del README para descargarlo desde Google Cloud Console.\n"
    )
    raise SystemExit(1)

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print(f"\n✅  token.json guardado en {TOKEN_FILE}")
print("    Ya puedes arrancar el servidor: python server.py\n")

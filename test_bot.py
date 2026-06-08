import urllib.request, json

data = json.dumps({"mensaje": "¿Cuánto cuesta un tinte?", "sesion": "test"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:5000/chat",
    data=data,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as r:
    respuesta = json.loads(r.read())

print("RESPUESTA DEL BOT:")
print(respuesta["respuesta"])

with open(r"C:\Users\gonza\Documents\chatbot-ventas\respuesta_bot.txt", "w", encoding="utf-8") as f:
    f.write(respuesta["respuesta"])

input("\nPresiona Enter para cerrar...")

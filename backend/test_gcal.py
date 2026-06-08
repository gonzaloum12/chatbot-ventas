"""
Punto de prueba: crea un evento real en Google Calendar y luego lo borra.
Ejecutar DESPUÉS de haber corrido auth_gcal.py.

    cd backend
    python test_gcal.py
"""
import datetime, gcal

# Fecha de prueba: mañana a las 10:00
manana = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
hora_prueba = "10:00"

print(f"\n→ Verificando disponibilidad para {manana} a las {hora_prueba}...")
libre = gcal.verificar_disponibilidad(manana, hora_prueba)
print(f"  Slot libre: {libre}")

if not libre:
    print("  ⚠️  Slot ocupado. Cambia hora_prueba en el script y vuelve a intentar.")
else:
    print("→ Creando evento de prueba...")
    event_id = gcal.crear_evento({
        "nombre": "Cliente Test",
        "telefono": "+34600000000",
        "servicio": "Prueba integración",
        "dia": manana,
        "hora": hora_prueba,
        "registrada": datetime.datetime.now().isoformat(timespec="seconds"),
    })
    print(f"  ✅  Evento creado. ID: {event_id}")
    print(f"  Abre Google Calendar y busca 'Prueba integración — Cliente Test' el {manana}.")

    # Limpieza: borrar el evento de prueba
    respuesta = input("\n¿Borrar el evento de prueba del calendario? [s/N]: ").strip().lower()
    if respuesta == "s":
        service = gcal._get_service()
        service.events().delete(calendarId=gcal.CALENDAR_ID, eventId=event_id).execute()
        print("  🗑️  Evento borrado.")
    else:
        print("  Evento conservado.")

from datetime import datetime
from eventos import BusEventos
from modelos import (Evento, LecturaHidrica, LECTURA_NUEVA, BOMBA_ENCENDIDA,
                     BOMBA_APAGADA, PARO_EMERGENCIA, FUGA_DETECTADA)
from observadores import ControlBomba, DetectorFugas, RegistroBD, NotificadorTelegram

bus = BusEventos()
control = ControlBomba(bus)
bd = RegistroBD()
telegram = NotificadorTelegram()

# Aquí se conecta cada módulo con los eventos que le interesan
bus.suscribir(LECTURA_NUEVA, control)
bus.suscribir(LECTURA_NUEVA, DetectorFugas(bus, control))
for tipo in (BOMBA_ENCENDIDA, BOMBA_APAGADA, PARO_EMERGENCIA, FUGA_DETECTADA):
    bus.suscribir(tipo, bd)
for tipo in (PARO_EMERGENCIA, FUGA_DETECTADA):
    bus.suscribir(tipo, telegram)

# Lecturas simuladas del ESP32: (hora, tinaco %, cisterna %, flujo L/min, corriente A)
lecturas = [
    (14, 20.0, 80.0, 0.0, 0.0),   # tinaco bajo -> prende bomba
    (14, 60.0, 70.0, 0.0, 2.1),   # llenando
    (15, 96.0, 60.0, 0.0, 2.0),   # tinaco lleno -> apaga
    (3, 90.0, 60.0, 0.4, 0.0),    # flujo de madrugada -> fuga
    (16, 20.0, 5.0, 0.0, 0.0),    # cisterna vacía -> paro anti-seco
]
for hora, tinaco, cisterna, flujo, corriente in lecturas:
    lectura = LecturaHidrica(datetime(2026, 10, 17, hora), tinaco, cisterna, flujo, corriente)
    bus.publicar(Evento(LECTURA_NUEVA, lectura))

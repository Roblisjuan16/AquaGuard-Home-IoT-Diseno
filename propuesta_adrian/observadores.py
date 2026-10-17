from eventos import Observador, BusEventos
from modelos import (Evento, LECTURA_NUEVA, BOMBA_ENCENDIDA, BOMBA_APAGADA,
                     PARO_EMERGENCIA, FUGA_DETECTADA)


class ControlBomba(Observador):
    """Escucha lecturas nuevas y decide si prende o apaga el relevador de 30A."""
    def __init__(self, bus: BusEventos):
        self.bus = bus
        self.encendida = False

    def actualizar(self, evento: Evento) -> None:
        l = evento.lectura
        if l.nivel_cisterna_pct < 10.0 and (self.encendida or l.nivel_tinaco_pct < 25.0):
            self._cambiar(False, evento, PARO_EMERGENCIA, "Cisterna baja (<10%). Paro anti-seco.")
        elif self.encendida and l.corriente_bomba_amp < 0.5:
            self._cambiar(False, evento, PARO_EMERGENCIA, "Corriente baja (SCT-013). Bomba en vacío.")
        elif l.nivel_tinaco_pct >= 95.0 and self.encendida:
            self._cambiar(False, evento, BOMBA_APAGADA, "Tinaco lleno.")
        elif l.nivel_tinaco_pct < 25.0 and not self.encendida:
            self._cambiar(True, evento, BOMBA_ENCENDIDA, "Llenado automático.")

    def _cambiar(self, encender: bool, evento: Evento, tipo: str, mensaje: str) -> None:
        self.encendida = encender
        self.bus.publicar(Evento(tipo, evento.lectura, mensaje))


class DetectorFugas(Observador):
    """Escucha lecturas nuevas y avisa si hay flujo de madrugada con la bomba apagada."""
    def __init__(self, bus: BusEventos, control: ControlBomba):
        self.bus = bus
        self.control = control

    def actualizar(self, evento: Evento) -> None:
        l = evento.lectura
        if 2 <= l.timestamp.hour <= 5 and l.flujo_l_min > 0.2 and not self.control.encendida:
            self.bus.publicar(Evento(FUGA_DETECTADA, l, f"Posible fuga nocturna ({l.flujo_l_min} L/min)."))


class RegistroBD(Observador):
    """Guarda en la base de datos todo lo que pasa."""
    def actualizar(self, evento: Evento) -> None:
        print(f"[BD] {evento.lectura.timestamp:%H:%M} {evento.tipo} {evento.mensaje}")


class NotificadorTelegram(Observador):
    """Manda alerta al residente solo cuando algo importa."""
    def actualizar(self, evento: Evento) -> None:
        print(f"[Telegram] {evento.mensaje}")

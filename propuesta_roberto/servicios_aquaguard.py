from abc import ABC, abstractmethod
from modelos import LecturaHidrica

class Notificador(ABC):
    @abstractmethod
    def enviar_alerta(self, mensaje: str) -> None:
        pass

class NotificadorTelegram(Notificador):
    """Responsabilidad única: Enviar alertas al residente vía Telegram."""
    def enviar_alerta(self, mensaje: str) -> None:
        print(f"[Telegram Bot] Alerta enviada: {mensaje}")

class LecturaRepository:
    """Responsabilidad única: Almacenar lecturas y eventos en la base de datos."""
    def guardar_lectura(self, lectura: LecturaHidrica) -> None:
        print(f"[Base de Datos] Lectura guardada ({lectura.timestamp.isoformat()})")

    def registrar_evento(self, evento: str) -> None:
        print(f"[Base de Datos] Evento registrado: {evento}")

class ControlBombaService:
    """Responsabilidad única: Evaluar reglas de llenado y paro de seguridad anti-seco."""
    def evaluar_y_controlar(self, lectura: LecturaHidrica) -> tuple[bool, str | None]:
        if lectura.nivel_cisterna_pct < 10.0:
            return False, "ALERTA: Cisterna baja (<10%). Paro anti-seco activado."
        if lectura.estado_bomba and lectura.corriente_bomba_amp < 0.5:
            return False, "ALERTA: Corriente anormal (SCT-013). Paro por vacío."
        if lectura.nivel_tinaco_pct >= 95.0:
            return False, None
        if lectura.nivel_tinaco_pct <= 25.0 and lectura.nivel_cisterna_pct >= 15.0:
            return True, None
        return lectura.estado_bomba, None

class AnaliticaHidricaService:
    """Responsabilidad única: Modelos de IA para detección de fugas y cálculo de autonomía."""
    def detectar_fuga_nocturna(self, lectura: LecturaHidrica) -> bool:
        hora = lectura.timestamp.hour
        if 2 <= hora <= 5 and lectura.flujo_l_min > 0.15 and not lectura.estado_bomba:
            return True
        return False

    def estimar_autonomia_dias(self, litros_disponibles: float, promedio_consumo_diario: float) -> float:
        return round(litros_disponibles / max(promedio_consumo_diario, 1.0), 1)

class ProcesadorTelemetriaFacade:
    """Responsabilidad única: Coordinar el flujo al recibir una lectura del ESP32."""
    def __init__(self, control_bomba: ControlBombaService, analitica: AnaliticaHidricaService,
                 repositorio: LecturaRepository, notificador: Notificador):
        self.control_bomba = control_bomba
        self.analitica = analitica
        self.repositorio = repositorio
        self.notificador = notificador

    def procesar_lectura_entrante(self, lectura: LecturaHidrica) -> None:
        self.repositorio.guardar_lectura(lectura)
        _, alerta = self.control_bomba.evaluar_y_controlar(lectura)
        if alerta:
            self.repositorio.registrar_evento(alerta)
            self.notificador.enviar_alerta(alerta)
        if self.analitica.detectar_fuga_nocturna(lectura):
            msg = f"Posible fuga silenciosa nocturna ({lectura.flujo_l_min} L/min)."
            self.repositorio.registrar_evento(msg)
            self.notificador.enviar_alerta(msg)
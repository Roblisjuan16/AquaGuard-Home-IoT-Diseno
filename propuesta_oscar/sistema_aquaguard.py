"""Orquestación de un ciclo de telemetría de AquaGuard Home IoT."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Mapping

from .componentes import ControladorBomba, DepositoAgua, MonitorFlujoTuberia
from .servicios import RepositorioDatos, ServicioAlertas


@dataclass(frozen=True)
class ResultadoMonitoreo:
    """Resultado tipado de procesar una lectura completa del sistema."""

    timestamp: datetime
    nivel_tinaco_pct: float
    nivel_cisterna_pct: float
    flujo_l_min: float
    corriente_amp: float
    estado_relevador: bool
    autonomia_dias: float
    alertas: tuple[str, ...]


class SistemaAquaGuard:
    """Coordina sensores, componentes físicos, persistencia y alertas."""

    def __init__(
        self,
        tinaco: DepositoAgua,
        cisterna: DepositoAgua,
        controlador_bomba: ControladorBomba,
        monitor_flujo: MonitorFlujoTuberia,
        repositorio: RepositorioDatos,
        servicio_alertas: ServicioAlertas,
    ) -> None:
        self.tinaco = tinaco
        self.cisterna = cisterna
        self.controlador_bomba = controlador_bomba
        self.monitor_flujo = monitor_flujo
        self.repositorio = repositorio
        self.servicio_alertas = servicio_alertas

    def procesar_ciclo_monitoreo(
        self, lecturas_raw: Mapping[str, object]
    ) -> ResultadoMonitoreo:
        """Convierte telemetría cruda, aplica control y registra sus resultados.

        Claves requeridas: ``dist_tinaco_cm``, ``dist_cisterna_cm``,
        ``flujo_l_min``, ``corriente_amp`` y ``consumo_diario_litros``.
        También admite ``timestamp`` (``datetime``) para reproducir lecturas.
        """
        distancia_tinaco = self._numero(lecturas_raw, "dist_tinaco_cm")
        distancia_cisterna = self._numero(lecturas_raw, "dist_cisterna_cm")
        flujo = self._numero(lecturas_raw, "flujo_l_min")
        corriente = self._numero(lecturas_raw, "corriente_amp")
        consumo_diario = self._numero(lecturas_raw, "consumo_diario_litros")
        if (
            distancia_tinaco < 0
            or distancia_cisterna < 0
            or flujo < 0
            or corriente < 0
        ):
            raise ValueError(
                "Las distancias, el flujo y la corriente no pueden ser negativos."
            )
        if consumo_diario <= 0:
            raise ValueError("'consumo_diario_litros' debe ser mayor que cero.")

        timestamp_raw = lecturas_raw.get("timestamp")
        if timestamp_raw is not None and not isinstance(timestamp_raw, datetime):
            raise ValueError("'timestamp' debe ser un objeto datetime.")
        timestamp = timestamp_raw or datetime.now().astimezone()

        nivel_tinaco = self.tinaco.calcular_porcentaje(distancia_tinaco)
        nivel_cisterna = self.cisterna.calcular_porcentaje(distancia_cisterna)
        proteccion_correcta = self.controlador_bomba.evaluar_proteccion_anti_seco(
            nivel_cisterna, corriente
        )

        mensajes: list[str] = []
        if not proteccion_correcta:
            if nivel_cisterna <= self.controlador_bomba.nivel_cisterna_critico_pct:
                mensaje = (
                    "Protección anti-seco: nivel crítico de cisterna; "
                    "bomba apagada."
                )
            else:
                mensaje = (
                    "Protección anti-seco: corriente de bomba por debajo del "
                    f"umbral ({corriente:.2f} A); bomba apagada."
                )
            mensajes.append(mensaje)
        else:
            self.controlador_bomba.determinar_encendido(
                nivel_tinaco, nivel_cisterna
            )

        if self.cisterna.es_nivel_critico():
            mensajes.append(
                f"Nivel crítico en {self.cisterna.nombre}: "
                f"{nivel_cisterna:.1f}%."
            )
        if self.tinaco.es_nivel_critico():
            mensajes.append(
                f"Nivel crítico en {self.tinaco.nombre}: {nivel_tinaco:.1f}%."
            )

        fuga_detectada = self.monitor_flujo.detectar_fuga_nocturna(
            flujo, timestamp
        ) and not self.controlador_bomba.estado_relevador
        if fuga_detectada:
            mensajes.append(
                f"Posible fuga nocturna: flujo de {flujo:.2f} L/min."
            )

        litros_disponibles = (
            self.tinaco.capacidad_litros * nivel_tinaco / 100
            + self.cisterna.capacidad_litros * nivel_cisterna / 100
        )
        autonomia = self.monitor_flujo.calcular_autonomia_dias(
            litros_disponibles, consumo_diario
        )

        registro: dict[str, object] = {
            "nivel_tinaco_pct": nivel_tinaco,
            "nivel_cisterna_pct": nivel_cisterna,
            "flujo_l_min": flujo,
            "corriente_amp": corriente,
            "estado_relevador": self.controlador_bomba.estado_relevador,
            "autonomia_dias": autonomia,
        }
        self.repositorio.guardar_lectura(registro, timestamp)
        for mensaje in mensajes:
            self.repositorio.registrar_evento(mensaje, timestamp)
            self.servicio_alertas.enviar_alerta(mensaje)

        return ResultadoMonitoreo(
            timestamp=timestamp,
            nivel_tinaco_pct=nivel_tinaco,
            nivel_cisterna_pct=nivel_cisterna,
            flujo_l_min=flujo,
            corriente_amp=corriente,
            estado_relevador=self.controlador_bomba.estado_relevador,
            autonomia_dias=autonomia,
            alertas=tuple(mensajes),
        )

    @staticmethod
    def _numero(lecturas: Mapping[str, object], clave: str) -> float:
        """Obtiene una lectura numérica y reporta claramente datos ausentes."""
        valor = lecturas.get(clave)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError(f"La lectura '{clave}' debe ser numérica.")
        numero = float(valor)
        if not isfinite(numero):
            raise ValueError(f"La lectura '{clave}' debe ser un número finito.")
        return numero


if __name__ == "__main__":
    tinaco = DepositoAgua("Tinaco", capacidad_litros=1100, altura_max_cm=150)
    cisterna = DepositoAgua("Cisterna", capacidad_litros=5000, altura_max_cm=200)
    sistema = SistemaAquaGuard(
        tinaco=tinaco,
        cisterna=cisterna,
        controlador_bomba=ControladorBomba(),
        monitor_flujo=MonitorFlujoTuberia(),
        repositorio=RepositorioDatos(),
        servicio_alertas=ServicioAlertas(),
    )
    resultado = sistema.procesar_ciclo_monitoreo(
        {
            "dist_tinaco_cm": 120,
            "dist_cisterna_cm": 50,
            "flujo_l_min": 0.0,
            "corriente_amp": 0.8,
            "consumo_diario_litros": 350,
        }
    )
    print(resultado)

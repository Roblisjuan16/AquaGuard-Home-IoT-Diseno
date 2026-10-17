"""Modelos de los componentes físicos principales de AquaGuard."""

from dataclasses import dataclass, field
from datetime import datetime, time
from math import isfinite


@dataclass
class DepositoAgua:
    """Representa un depósito medido con un sensor ultrasónico JSN-SR04T.

    ``altura_max_cm`` es la altura útil entre el sensor y el nivel máximo de
    agua. La distancia recibida corresponde al espacio vacío sobre el agua.
    """

    nombre: str
    capacidad_litros: float
    altura_max_cm: float
    nivel_critico_pct: float = 10.0
    nivel_actual_pct: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El nombre del depósito no puede estar vacío.")
        if not isfinite(self.capacidad_litros) or self.capacidad_litros <= 0:
            raise ValueError("La capacidad debe ser mayor que cero.")
        if not isfinite(self.altura_max_cm) or self.altura_max_cm <= 0:
            raise ValueError("La altura máxima debe ser mayor que cero.")
        if (
            not isfinite(self.nivel_critico_pct)
            or not 0 <= self.nivel_critico_pct <= 100
        ):
            raise ValueError("El nivel crítico debe estar entre 0 y 100%.")

    def calcular_porcentaje(self, distancia_cm: float) -> float:
        """Calcula y almacena el nivel de agua porcentual desde la distancia.

        Las mediciones por encima del máximo o por debajo del mínimo útil se
        limitan al intervalo 0–100%, tal como se espera de la geometría del
        depósito.
        """
        if not isfinite(distancia_cm) or distancia_cm < 0:
            raise ValueError("La distancia del sensor no puede ser negativa.")
        nivel = (self.altura_max_cm - distancia_cm) / self.altura_max_cm * 100
        self.nivel_actual_pct = min(100.0, max(0.0, nivel))
        return self.nivel_actual_pct

    def es_nivel_critico(self) -> bool:
        """Indica si la última lectura está en el umbral crítico configurado."""
        return self.nivel_actual_pct <= self.nivel_critico_pct


@dataclass
class ControladorBomba:
    """Modela el relevador de 30 A y la protección de la bomba.

    Los niveles de cisterna y tinaco se expresan en porcentaje. La corriente
    se mide en amperios mediante el sensor SCT-013.
    """

    estado_relevador: bool = False
    umbral_corriente_min: float = 0.5
    nivel_cisterna_critico_pct: float = 10.0
    nivel_cisterna_arranque_pct: float = 15.0
    nivel_tinaco_arranque_pct: float = 25.0
    nivel_tinaco_lleno_pct: float = 95.0

    def __post_init__(self) -> None:
        if not isfinite(self.umbral_corriente_min) or self.umbral_corriente_min < 0:
            raise ValueError("El umbral de corriente no puede ser negativo.")
        for nombre, nivel in (
            ("crítico de cisterna", self.nivel_cisterna_critico_pct),
            ("arranque de cisterna", self.nivel_cisterna_arranque_pct),
            ("arranque de tinaco", self.nivel_tinaco_arranque_pct),
            ("tinaco lleno", self.nivel_tinaco_lleno_pct),
        ):
            if not isfinite(nivel) or not 0 <= nivel <= 100:
                raise ValueError(f"El nivel de {nombre} debe estar entre 0 y 100%.")

    def evaluar_proteccion_anti_seco(
        self, nivel_cisterna: float, corriente_amp: float
    ) -> bool:
        """Protege la bomba ante cisterna crítica o corriente anormal.

        Devuelve ``False`` y apaga el relevador si detecta una condición
        insegura; en caso contrario devuelve ``True``. La corriente solo se
        evalúa cuando el relevador está encendido.
        """
        if (
            not isfinite(nivel_cisterna)
            or not 0 <= nivel_cisterna <= 100
        ):
            raise ValueError("El nivel de cisterna debe estar entre 0 y 100%.")
        if not isfinite(corriente_amp) or corriente_amp < 0:
            raise ValueError("La corriente no puede ser negativa.")

        cisterna_baja = nivel_cisterna <= self.nivel_cisterna_critico_pct
        corriente_anormal = (
            self.estado_relevador and corriente_amp < self.umbral_corriente_min
        )
        if cisterna_baja or corriente_anormal:
            self.estado_relevador = False
            return False
        return True

    def determinar_encendido(
        self, nivel_tinaco: float, nivel_cisterna: float
    ) -> bool:
        """Aplica el control automático con histéresis de llenado."""
        if (
            not isfinite(nivel_tinaco)
            or not isfinite(nivel_cisterna)
            or not 0 <= nivel_tinaco <= 100
            or not 0 <= nivel_cisterna <= 100
        ):
            raise ValueError("Los niveles deben estar entre 0 y 100%.")
        if nivel_tinaco >= self.nivel_tinaco_lleno_pct:
            self.estado_relevador = False
        elif nivel_cisterna < self.nivel_cisterna_arranque_pct:
            self.estado_relevador = False
        elif nivel_tinaco <= self.nivel_tinaco_arranque_pct:
            self.estado_relevador = True
        return self.estado_relevador


@dataclass
class MonitorFlujoTuberia:
    """Representa el medidor de flujo YF-S201 instalado en la tubería."""

    flujo_l_min: float = 0.0
    umbral_fuga_l_min: float = 0.15

    def __post_init__(self) -> None:
        if self.flujo_l_min < 0:
            raise ValueError("El flujo no puede ser negativo.")
        if not isfinite(self.umbral_fuga_l_min) or self.umbral_fuga_l_min < 0:
            raise ValueError("El umbral de fuga no puede ser negativo.")

    def detectar_fuga_nocturna(
        self, flujo: float, hora: int | time | datetime
    ) -> bool:
        """Detecta flujo persistente entre las 02:00 (incluida) y las 05:00.

        ``hora`` puede ser una hora entera de 0 a 23, un ``datetime`` o un
        ``time``. El valor de flujo recibido queda almacenado en el monitor.
        """
        if not isfinite(flujo) or flujo < 0:
            raise ValueError("El flujo no puede ser negativo.")
        if isinstance(hora, datetime):
            hora_numero = hora.hour
        elif isinstance(hora, time):
            hora_numero = hora.hour
        elif isinstance(hora, int) and 0 <= hora <= 23:
            hora_numero = hora
        else:
            raise ValueError("La hora debe ser un entero de 0 a 23 o una hora.")

        self.flujo_l_min = flujo
        return 2 <= hora_numero < 5 and flujo > self.umbral_fuga_l_min

    def calcular_autonomia_dias(
        self, litros_totales: float, consumo_diario: float
    ) -> float:
        """Estima los días de autonomía usando el consumo diario en litros."""
        if not isfinite(litros_totales) or litros_totales < 0:
            raise ValueError("Los litros disponibles no pueden ser negativos.")
        if not isfinite(consumo_diario) or consumo_diario <= 0:
            raise ValueError("El consumo diario debe ser mayor que cero.")
        return round(litros_totales / consumo_diario, 1)

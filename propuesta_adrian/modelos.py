from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LecturaHidrica:
    """Lectura que manda el nodo ESP32 con los sensores de AquaGuard."""
    timestamp: datetime
    nivel_tinaco_pct: float       # Sensor ultrasónico JSN-SR04T
    nivel_cisterna_pct: float     # Sensor ultrasónico JSN-SR04T
    flujo_l_min: float            # Sensor de flujo YF-S201
    corriente_bomba_amp: float    # Sensor de corriente SCT-013


@dataclass(frozen=True)
class Evento:
    """Algo que pasó en el sistema y que otros módulos pueden escuchar."""
    tipo: str
    lectura: LecturaHidrica
    mensaje: str = ""


# Tipos de evento
LECTURA_NUEVA = "lectura_nueva"
BOMBA_ENCENDIDA = "bomba_encendida"
BOMBA_APAGADA = "bomba_apagada"
PARO_EMERGENCIA = "paro_emergencia"
FUGA_DETECTADA = "fuga_detectada"

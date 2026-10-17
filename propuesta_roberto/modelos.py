from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class LecturaHidrica:
    """Representa el registro de lecturas de los sensores IoT de AquaGuard."""
    timestamp: datetime
    nivel_tinaco_pct: float       # Sensor ultrasónico JSN-SR04T
    nivel_cisterna_pct: float     # Sensor ultrasónico JSN-SR04T
    flujo_l_min: float            # Sensor de flujo YF-S201
    corriente_bomba_amp: float    # Sensor de corriente SCT-013
    estado_bomba: bool            # Relevador de 30A
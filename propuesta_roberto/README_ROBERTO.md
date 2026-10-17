# Propuesta de Mejora — Roberto Carlo Lisjuán Pérez

## 1. Diagrama Diseño Original (Monolítico)
```mermaid
classDiagram
    class AquaGuardMonolitico {
        +bool estado_bomba
        +recibir_y_procesar_lectura_esp32(dist_tinaco, dist_cisterna)
        +controlar_bomba(porcentaje_tinaco, porcentaje_cisterna, corriente)
        +detectar_fugas_y_calcular_autonomia(flujo, hora, consumo, litros)
        +guardar_en_base_datos(nivel_tinaco, nivel_cisterna, flujo, corriente)
        +enviar_alerta_usuario(mensaje)
    }
```

## 2. Diagrama Diseño Mejorado (Propuesta Roberto)
```mermaid
classDiagram
    class LecturaHidrica {
        <<dataclass>>
        +datetime timestamp
        +float nivel_tinaco_pct
        +float nivel_cisterna_pct
        +float flujo_l_min
        +float corriente_bomba_amp
        +bool estado_bomba
    }
    class Notificador {
        <<interface>>
        +enviar_alerta(mensaje: str)*
    }
    class NotificadorTelegram {
        +enviar_alerta(mensaje: str)
    }
    class LecturaRepository {
        +guardar_lectura(lectura: LecturaHidrica)
        +registrar_evento(evento: str)
    }
    class ControlBombaService {
        +evaluar_y_controlar(lectura: LecturaHidrica) tuple
    }
    class AnaliticaHidricaService {
        +detectar_fuga_nocturna(lectura: LecturaHidrica) bool
        +estimar_autonomia_dias(litros: float, promedio: float) float
    }
    class ProcesadorTelemetriaFacade {
        +procesar_lectura_entrante(lectura: LecturaHidrica)
    }

    Notificador <|.. NotificadorTelegram
    ProcesadorTelemetriaFacade --> ControlBombaService
    ProcesadorTelemetriaFacade --> AnaliticaHidricaService
    ProcesadorTelemetriaFacade --> LecturaRepository
    ProcesadorTelemetriaFacade --> Notificador
```

## 3. Justificación Técnica
* **Mantenimiento:** Separar `AnaliticaHidricaService` de `ControlBombaService` permite ajustar modelos de IA sin arriesgar las reglas eléctricas de protección anti-seco.
* **Pruebas (Testing):** La inyección de dependencias en `ProcesadorTelemetriaFacade` permite simular la base de datos y alertas mediante *Mocks*.
* **Reutilización y Escalabilidad:** La interfaz `Notificador` permite añadir alertas por correo o WhatsApp sin modificar las clases existentes.
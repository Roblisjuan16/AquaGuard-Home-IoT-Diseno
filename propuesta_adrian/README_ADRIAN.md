# Propuesta de Mejora — José Adrián Caleano Luna

Arquitectura basada en eventos con el patrón **Observer**.

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

## 2. Diagrama Diseño Mejorado (Propuesta Adrián)
```mermaid
classDiagram
    class LecturaHidrica {
        <<dataclass>>
        +datetime timestamp
        +float nivel_tinaco_pct
        +float nivel_cisterna_pct
        +float flujo_l_min
        +float corriente_bomba_amp
    }
    class Evento {
        <<dataclass>>
        +str tipo
        +LecturaHidrica lectura
        +str mensaje
    }
    class Observador {
        <<interface>>
        +actualizar(evento: Evento)*
    }
    class BusEventos {
        -dict suscriptores
        +suscribir(tipo: str, observador: Observador)
        +publicar(evento: Evento)
    }
    class ControlBomba {
        +bool encendida
        +actualizar(evento: Evento)
    }
    class DetectorFugas {
        +actualizar(evento: Evento)
    }
    class RegistroBD {
        +actualizar(evento: Evento)
    }
    class NotificadorTelegram {
        +actualizar(evento: Evento)
    }

    Observador <|.. ControlBomba
    Observador <|.. DetectorFugas
    Observador <|.. RegistroBD
    Observador <|.. NotificadorTelegram
    BusEventos o--> Observador : avisa a
    ControlBomba --> BusEventos : publica
    DetectorFugas --> BusEventos : publica
    Evento --> LecturaHidrica
```

## 3. Cómo funciona
1. El ESP32 manda una lectura y se publica el evento `lectura_nueva` en el `BusEventos`.
2. `ControlBomba` y `DetectorFugas` están suscritos a `lectura_nueva`. Cada uno revisa la lectura por su lado.
3. Si pasa algo, publican su propio evento: `bomba_encendida`, `bomba_apagada`, `paro_emergencia` o `fuga_detectada`.
4. `RegistroBD` guarda todos esos eventos y `NotificadorTelegram` solo avisa al residente de los importantes (paro de emergencia y fuga).

Para probarlo: `cd propuesta_adrian && python3 main.py`

```
[BD] 14:00 bomba_encendida Llenado automático.
[BD] 15:00 bomba_apagada Tinaco lleno.
[BD] 03:00 fuga_detectada Posible fuga nocturna (0.4 L/min).
[Telegram] Posible fuga nocturna (0.4 L/min).
[BD] 16:00 paro_emergencia Cisterna baja (<10%). Paro anti-seco.
[Telegram] Cisterna baja (<10%). Paro anti-seco.
```

## 4. Justificación Técnica
* **Bajo acoplamiento:** los módulos no se conocen entre sí, solo conocen el bus. `ControlBomba` no sabe que existe la base de datos ni Telegram.
* **Extensibilidad:** para agregar alertas por correo o un dashboard se crea un nuevo `Observador` y se suscribe en `main.py`, sin tocar las clases que ya existen (principio abierto/cerrado).
* **Pruebas (Testing):** cada observador se prueba solo, mandándole un `Evento` armado a mano.
* **Encaja con IoT:** el ESP32 ya trabaja mandando lecturas cada cierto tiempo, así que pensar el sistema como eventos que llegan y se reparten es natural.
* **Diferencia con la Fachada:** en la propuesta de Roberto la fachada decide el orden y llama a cada servicio. Aquí nadie coordina; cada módulo reacciona a lo que le interesa.

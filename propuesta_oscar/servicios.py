"""Adaptadores simulados de persistencia y notificación de AquaGuard."""

from datetime import datetime
from typing import Mapping


class RepositorioDatos:
    """Simula el almacenamiento de lecturas y eventos con marca de tiempo."""

    def __init__(self) -> None:
        self.lecturas: list[dict[str, object]] = []
        self.eventos: list[dict[str, str]] = []

    def guardar_lectura(
        self, lectura: Mapping[str, object], timestamp: datetime | None = None
    ) -> dict[str, object]:
        """Almacena una copia de la lectura junto con su timestamp."""
        fecha = timestamp or datetime.now().astimezone()
        registro: dict[str, object] = {
            **lectura,
            "timestamp": fecha.isoformat(),
        }
        self.lecturas.append(registro)
        return registro

    def registrar_evento(
        self, mensaje: str, timestamp: datetime | None = None
    ) -> dict[str, str]:
        """Almacena un evento y la hora en que se produjo."""
        fecha = timestamp or datetime.now().astimezone()
        evento = {"timestamp": fecha.isoformat(), "mensaje": mensaje}
        self.eventos.append(evento)
        return evento


class ServicioAlertas:
    """Simula notificaciones Telegram/correo sin conectarse a servicios externos.

    Las alertas se conservan en memoria para facilitar pruebas y permitir que
    un adaptador de transporte real se integre posteriormente.
    """

    def __init__(self) -> None:
        self.alertas_enviadas: list[str] = []

    def enviar_alerta(self, mensaje: str) -> None:
        """Registra una notificación simulada para Telegram y correo."""
        if not mensaje.strip():
            raise ValueError("El mensaje de alerta no puede estar vacío.")
        self.alertas_enviadas.append(mensaje)

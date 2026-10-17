from abc import ABC, abstractmethod
from collections import defaultdict
from modelos import Evento


class Observador(ABC):
    """Cualquier módulo que quiera enterarse de un evento."""
    @abstractmethod
    def actualizar(self, evento: Evento) -> None:
        pass


class BusEventos:
    """Sujeto del patrón Observer: guarda quién escucha cada evento y les avisa."""
    def __init__(self):
        self._suscriptores = defaultdict(list)

    def suscribir(self, tipo: str, observador: Observador) -> None:
        self._suscriptores[tipo].append(observador)

    def publicar(self, evento: Evento) -> None:
        for observador in self._suscriptores[evento.tipo]:
            observador.actualizar(evento)

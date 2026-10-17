from datetime import datetime

class AquaGuardMonolitico:
    """
    DISEÑO ORIGINAL (PROBLEMA DE DISEÑO: CLASE DIOS / GOD OBJECT)
    Concentra recepción del ESP32, control de la bomba, modelos de IA,
    almacenamiento en base de datos y envío de alertas en una sola clase.
    """
    def __init__(self):
        self.estado_bomba = False

    def recibir_y_procesar_lectura_esp32(self, dist_tinaco_cm: float, dist_cisterna_cm: float):
        print("Recibiendo datos por WiFi desde el nodo ESP32...")
        porcentaje_tinaco = max(0.0, min(100.0, (100.0 - dist_tinaco_cm)))
        porcentaje_cisterna = max(0.0, min(100.0, (200.0 - dist_cisterna_cm) / 2.0))
        return porcentaje_tinaco, porcentaje_cisterna

    def controlar_bomba(self, porcentaje_tinaco: float, porcentaje_cisterna: float, corriente_amp: float):
        if porcentaje_cisterna < 10.0 or (self.estado_bomba and corriente_amp < 0.5):
            self.estado_bomba = False
            print("[RELEVADOR 30A] PARO ANTI-SECO: Bomba apagada de emergencia.")
        elif porcentaje_tinaco < 25.0 and porcentaje_cisterna >= 10.0:
            self.estado_bomba = True
            print("[RELEVADOR 30A] LLENADO AUTOMÁTICO: Bomba encendida.")
        elif porcentaje_tinaco >= 95.0:
            self.estado_bomba = False
            print("[RELEVADOR 30A] TINACO LLENO: Bomba apagada.")

    def detectar_fugas_y_calcular_autonomia(self, flujo_l_min: float, hora_actual: int, consumo_diario: float, litros: float):
        if 2 <= hora_actual <= 5 and flujo_l_min > 0.2 and not self.estado_bomba:
            print("[IA - ISOLATION FOREST] Anomalía detectada: Posible fuga nocturna.")
        dias_autonomia = litros / max(consumo_diario, 1.0)
        return dias_autonomia

    def guardar_en_base_datos(self, nivel_tinaco: float, nivel_cisterna: float, flujo: float, corriente: float):
        timestamp = datetime.now().isoformat()
        print(f"[BD] Guardando registro: {timestamp} | Tinaco: {nivel_tinaco}% | Cisterna: {nivel_cisterna}%")

    def enviar_alerta_usuario(self, mensaje: str):
        print(f"[TELEGRAM / CORREO] Alerta enviada: {mensaje}")
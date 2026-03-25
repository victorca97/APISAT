import logging
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

class Logger:
    def __init__(self):
        """Inicializa el logger con logs diarios guardados en la carpeta /logs del proyecto"""

        # Ruta a la raíz del proyecto (2 niveles arriba del archivo actual)
        raiz_proyecto = Path(__file__).resolve().parent.parent
        carpeta_log = raiz_proyecto / "logs"
        carpeta_log.mkdir(parents=True, exist_ok=True)  # Crea la carpeta si no existe

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = carpeta_log / f"BOT-SAT ({fecha_hoy}).log"

        # Crear el logger
        self.logger = logging.getLogger("LoggerGlobal")
        self.logger.setLevel(logging.DEBUG)
        
        # ¡¡¡ESTO ES CLAVE!!! Evita que el logger imprima a la consola automáticamente
        self.logger.propagate = False

        # Formato para el archivo de log
        class CustomFormatter(logging.Formatter):
            def format(self, record):
                if record.levelname == "WARNING":
                    record.levelname = "OBSERVACION"

                nivel_max_len = 11  # Longitud máxima del nivel
                nivel_formateado = record.levelname.ljust(nivel_max_len)
                
                # Fecha y hora completa con milisegundos
                fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]
                lineas = record.msg.split("\n")
                primera_linea = f"{fecha_hora_actual} - {nivel_formateado} - {lineas[0]}"
                espacios = " " * len(fecha_hora_actual + " - " + nivel_formateado + " - ")
                lineas_extra = "\n".join(f"{espacios}{linea}" for linea in lineas[1:])

                return primera_linea + ("\n" + lineas_extra if lineas_extra else "")

        formato = CustomFormatter("%(message)s")

        manejador_archivo = logging.FileHandler(str(nombre_archivo), mode="a", encoding="utf-8")
        manejador_archivo.setFormatter(formato)
        self.logger.addHandler(manejador_archivo)

    class ColoredFormatter:
        COLORS = {
            "DEBUG": Fore.BLUE,
            "INFO": Fore.GREEN,
            "OBS": Fore.YELLOW,
            "ERROR": Fore.RED,
            "WARNING": Fore.YELLOW
        }

        @staticmethod
        def format(level, message):
            nivel_max_len = 5
            display_level = "OBSERVACION" if level.upper() == "WARNING" else level.upper()
            nivel_formateado = display_level.ljust(nivel_max_len)
            
            # Fecha y hora completa con milisegundos (igual que en archivo)
            fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]

            lineas = message.split("\n")
            primera_linea = f"{fecha_hora_actual} - {nivel_formateado} - {lineas[0]}"
            espacios = " " * len(fecha_hora_actual + " - " + nivel_formateado + " - ")
            lineas_extra = "\n".join(f"{espacios}{linea}" for linea in lineas[1:])
            mensaje_alineado = primera_linea + ("\n" + lineas_extra if lineas_extra else "")

            color = Logger.ColoredFormatter.COLORS.get(level.upper(), Fore.WHITE)
            return f"{color}{mensaje_alineado}{Style.RESET_ALL}"

    def _log(self, level, message, condicion=False):
        """Método interno para manejar los logs"""
        # Escribir en el archivo
        getattr(self.logger, level.lower())(message)

        # Mostrar en consola (si no está condicionado)
        if not condicion:
            print(self.ColoredFormatter.format(level, message))

    def debug(self, mensaje, condicion=False):
        self._log("DEBUG", mensaje, condicion)

    def info(self, mensaje, condicion=False):
        self._log("INFO", mensaje, condicion)

    def warning(self, mensaje, condicion=False):
        self._log("WARNING", mensaje, condicion)

    def error(self, mensaje, condicion=False):
        self._log("ERROR", mensaje, condicion)


# Instancia global del logger
Registrador = Logger()
import logging
import colorlog
from modules.config.config import Config  # Konfigurationsklasse importieren

# Benutzerdefiniertes Log-Level für SUCCESS hinzufügen
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)

logging.Logger.success = success

# Logger einrichten und Log-Level aus Config laden
def setup_logger():
    # Log-Level aus Config-Klasse laden
    log_level_str = Config.LOG_LEVEL
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Formatter-Format für das gewünschte Ausgabeformat
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(filename)s[%(lineno)d]\t- %(levelname)s | %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'yellow',
            'SUCCESS': 'green',
            'WARNING': 'blue',
            'ERROR': 'red',
            'CRITICAL': 'bold_red'
        },
        datefmt='%H:%M:%S'  # Uhrzeit ohne Datum
    ))

    # Logger konfigurieren
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger

# Logger für Testzwecke
logger = setup_logger()
import logging

def setup_logging(level=logging.INFO):
    # La fonction logging.basicConfig ne configure pas le root logger si un handler existe déjà,
    # ce qui arrive souvent sur Railway ou d'autres environnements qui préconfigurent le logging.
    # Pour forcer la configuration, il faut explicitement supprimer les handlers existants du root logger.
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
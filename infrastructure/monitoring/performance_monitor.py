import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Moniteur de performance pour suivre les opérations."""

    @contextmanager
    def track_operation(self, operation_name: str):
        """Contexte manager pour suivre la durée d'une opération."
        Args:
            operation_name: Nom de l'opération à suivre.
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000  # en millisecondes
            logger.info(f"Performance: Operation '{operation_name}' took {duration:.2f} ms")

    def log_error(self, error_message: str, details: dict = None):
        """Log une erreur."
        Args:
            error_message: Message d'erreur.
            details: Détails supplémentaires de l'erreur.
        """
        if details:
            logger.error(f"Error: {error_message} - Details: {details}")
        else:
            logger.error(f"Error: {error_message}")

    def log_performance(self, metric_name: str, value: float, tags: dict = None):
        """Log une métrique de performance."
        Args:
            metric_name: Nom de la métrique.
            value: Valeur de la métrique.
            tags: Tags associés à la métrique.
        """
        if tags:
            logger.info(f"Metric: {metric_name} = {value} (Tags: {tags})")
        else:
            logger.info(f"Metric: {metric_name} = {value}")

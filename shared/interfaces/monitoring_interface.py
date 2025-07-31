from typing import Protocol

class MonitoringInterface(Protocol):
    def track_operation(self, operation_name: str):
        ...

    def log_error(self, error_message: str, details: dict = None):
        ...

    def log_performance(self, metric_name: str, value: float, tags: dict = None):
        ...

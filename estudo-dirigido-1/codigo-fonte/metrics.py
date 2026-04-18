"""
Medicao de desempenho: tempo de parede e pico aproximado de memoria alocada (tracemalloc).

Os algoritmos de busca devolvem estatisticas estruturais (nos expandidos, tamanho da fronteira).
Este modulo encapsula a execucao para manter a contabilidade de recursos em um so lugar.
"""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ResourceMetrics:
    wall_time_sec: float
    peak_traced_memory_bytes: int


def measure_callable(func: Callable[[], T]) -> tuple[T, ResourceMetrics]:
    """Executa `func`, medindo tempo e pico de memoria rastreada pelo interpretador."""
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        result = func()
    finally:
        wall = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return result, ResourceMetrics(wall_time_sec=wall, peak_traced_memory_bytes=peak)

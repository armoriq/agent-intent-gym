"""Optional native benchmark adapters. Upstream packages are imported only when selected."""

from .models import BenchmarkConfig
from .registry import benchmark_catalog
from .runner import run_benchmark

__all__ = ["BenchmarkConfig", "benchmark_catalog", "run_benchmark"]

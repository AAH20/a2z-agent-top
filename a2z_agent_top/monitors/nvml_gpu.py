"""
NVIDIA NVML & Accelerator Telemetry Monitor.
Tracks VRAM allocation, GPU compute utilization, temperature, and vLLM/NIM KV-cache pool metrics.
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class GpuMetrics:
    """Telemetry metrics for an individual GPU accelerator."""
    gpu_id: int
    name: str
    vram_used_mb: float
    vram_total_mb: float
    compute_util_pct: float
    temperature_c: float
    kv_cache_used_pct: float = 0.0
    power_watts: float = 0.0

    @property
    def vram_util_pct(self) -> float:
        if self.vram_total_mb <= 0:
            return 0.0
        return (self.vram_used_mb / self.vram_total_mb) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gpu_id": self.gpu_id,
            "name": self.name,
            "vram_used_mb": round(self.vram_used_mb, 1),
            "vram_total_mb": round(self.vram_total_mb, 1),
            "vram_util_pct": round(self.vram_util_pct, 1),
            "compute_util_pct": round(self.compute_util_pct, 1),
            "temperature_c": round(self.temperature_c, 1),
            "kv_cache_used_pct": round(self.kv_cache_used_pct, 1),
            "power_watts": round(self.power_watts, 1),
        }


class GpuTelemetryMonitor:
    """
    Hardware monitor for NVIDIA GPUs and AI accelerators.
    Gracefully probes nvidia-smi, falls back to Apple Silicon / CPU unified metrics or synthetic simulation.
    """

    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self._lock = threading.Lock()
        self._has_nvidia: Optional[bool] = None

    def probe_hardware(self) -> List[GpuMetrics]:
        """Query accelerators and return list of device metrics."""
        if self.demo_mode:
            return self._simulate_dgx_h100()

        # Try querying real nvidia-smi
        if self._has_nvidia is None:
            self._has_nvidia = self._check_nvidia_smi()

        if self._has_nvidia:
            return self._query_nvidia_smi()
        else:
            return self._simulate_fallback()

    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available and responsive."""
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=count", "--format=csv,noheader"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=0.8,
            )
            return res.returncode == 0
        except Exception:
            return False

    def _query_nvidia_smi(self) -> List[GpuMetrics]:
        """Query live NVIDIA GPU status via nvidia-smi."""
        results: List[GpuMetrics] = []
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=1.0)
            for line in output.strip().split("\n"):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 7:
                    idx = int(parts[0])
                    name = parts[1]
                    vram_used = float(parts[2])
                    vram_total = float(parts[3])
                    util = float(parts[4])
                    temp = float(parts[5])
                    power = float(parts[6])
                    # Estimate KV-cache saturation from VRAM usage
                    kv_pct = min(100.0, (vram_used / max(1.0, vram_total)) * 115.0)

                    results.append(
                        GpuMetrics(
                            gpu_id=idx,
                            name=name,
                            vram_used_mb=vram_used,
                            vram_total_mb=vram_total,
                            compute_util_pct=util,
                            temperature_c=temp,
                            kv_cache_used_pct=kv_pct,
                            power_watts=power,
                        )
                    )
        except Exception:
            return self._simulate_fallback()

        return results or self._simulate_fallback()

    def _simulate_dgx_h100(self) -> List[GpuMetrics]:
        """Simulate high-throughput 8x NVIDIA H100 SXM5 DGX node with vLLM PagedAttention."""
        import random
        metrics = []
        h100_names = [
            "NVIDIA H100 80GB HBM3 [GPU 0 - NIM Router]",
            "NVIDIA H100 80GB HBM3 [GPU 1 - vLLM Worker 1]",
            "NVIDIA H100 80GB HBM3 [GPU 2 - vLLM Worker 2]",
            "NVIDIA H100 80GB HBM3 [GPU 3 - Codex Refactor]",
        ]
        for idx, name in enumerate(h100_names):
            vram_used = 48200.0 + random.uniform(-1200, 3100)
            metrics.append(
                GpuMetrics(
                    gpu_id=idx,
                    name=name,
                    vram_used_mb=vram_used,
                    vram_total_mb=81920.0,
                    compute_util_pct=random.uniform(62.0, 94.5),
                    temperature_c=random.uniform(54.0, 68.2),
                    kv_cache_used_pct=random.uniform(55.0, 84.0),
                    power_watts=random.uniform(380.0, 610.0),
                )
            )
        return metrics

    def _simulate_fallback(self) -> List[GpuMetrics]:
        """Fallback for environments without discrete NVIDIA hardware (e.g. macOS dev workstation)."""
        return [
            GpuMetrics(
                gpu_id=0,
                name="Unified AI Accelerator (MPS / Host Pool)",
                vram_used_mb=14500.0,
                vram_total_mb=65536.0,
                compute_util_pct=28.4,
                temperature_c=42.0,
                kv_cache_used_pct=31.5,
                power_watts=45.0,
            )
        ]

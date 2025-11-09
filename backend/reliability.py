
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional
from math import exp
import os, time
import matplotlib
matplotlib.use("Agg")  # No display server required
import matplotlib.pyplot as plt

# NOTA DE ESTILO: Cumple con la restricción de usar exclusivamente Matplotlib,
# sin seaborn y sin especificar colores/manual styles.

@dataclass
class PartWeibull:
    # Parámetros de Weibull para km y meses
    k_km: float
    p_at_interval_km: float  # Probabilidad acumulada deseada en el intervalo recomendado (calibración)
    k_month: Optional[float] = None
    p_at_interval_month: Optional[float] = None

# Parámetros iniciales (heurísticos) por autoparte
# La calibración fija la escala lambda para que F(intervalo)=p_at_interval
_PARTS: Dict[str, PartWeibull] = {
    "aceite": PartWeibull(k_km=2.0, p_at_interval_km=0.12, k_month=1.8, p_at_interval_month=0.12),
    "frenos": PartWeibull(k_km=1.8, p_at_interval_km=0.20, k_month=1.6, p_at_interval_month=0.18),
    "correa": PartWeibull(k_km=3.0, p_at_interval_km=0.05, k_month=2.8, p_at_interval_month=0.05),
    "bateria": PartWeibull(k_km=1.2, p_at_interval_km=0.08, k_month=2.2, p_at_interval_month=0.20),
    "neumaticos": PartWeibull(k_km=1.6, p_at_interval_km=0.20, k_month=1.4, p_at_interval_month=0.18),
    "filtro_aire": PartWeibull(k_km=1.3, p_at_interval_km=0.30, k_month=1.1, p_at_interval_month=0.25),
    "refrigerante_mangueras": PartWeibull(k_km=1.4, p_at_interval_km=0.10, k_month=1.8, p_at_interval_month=0.10),
}

def _calibrate_lambda(interval_value: float, k: float, p_at_interval: float) -> float:
    """Calcula lambda tal que F(interval)=p usando Weibull: F(t)=1-exp(-(t/lambda)^k)."""
    if interval_value <= 0:
        interval_value = 1.0
    p = max(1e-6, min(0.95, p_at_interval))
    # 1 - exp(-(x/l)^k) = p  -> exp(-(x/l)^k) = 1-p -> (x/l)^k = -ln(1-p)
    # l = x / (-ln(1-p))**(1/k)
    from math import log
    l = interval_value / ((-log(1.0 - p)) ** (1.0 / k))
    return max(l, 1e-3)

def _weibull_F(t, lam, k):
    if t <= 0:
        return 0.0
    from math import exp
    return 1.0 - exp(- (t / lam) ** k)

def _conditional_failure_probability(t_now, delta, lam, k) -> float:
    """P(t_now < T <= t_now+delta | T > t_now)."""
    F_now = _weibull_F(t_now, lam, k)
    F_future = _weibull_F(t_now + delta, lam, k)
    survival_now = max(1e-9, 1.0 - F_now)
    return max(0.0, min(1.0, (F_future - F_now) / survival_now))

def _apply_context_adjustments(part: str, lam_km: float, lam_month: Optional[float], clima: Optional[str]) -> Tuple[float, Optional[float]]:
    """Ajustes simples por clima (afecta vida útil efectiva)."""
    factor = 1.0
    if clima:
        c = clima.lower()
        # Calor o frío extremos castigan batería y llantas
        if part in ("bateria", "neumaticos"):
            if c in ("calido", "muy_calido", "desierto", "frio", "muy_frio"):
                factor = 0.85  # 15% menos de vida útil efectiva
            elif c in ("templado",):
                factor = 1.0
        # Goma/mangueras también algo sensibles
        if part == "refrigerante_mangueras" and c in ("calido", "muy_calido"):
            factor = 0.9
    return lam_km * factor, (lam_month * factor if lam_month else lam_month)

def project_failure_curve(
    part_type: str,
    current_km: float,
    last_service_km: float,
    service_interval_km: float,
    months_since_service: Optional[float] = None,
    service_interval_months: Optional[float] = None,
    clima: Optional[str] = None,
    horizon_km: Optional[float] = None,
    points: int = 201,
):
    """Devuelve puntos (x_km, riesgo_en_% a condición de sobrevivir hasta hoy) y metadatos.
    Calcula sobre km; si se dan meses, adjunta resumen temporal."""
    part_type = part_type.lower()
    if part_type not in _PARTS:
        raise ValueError(f"Autoparte no soportada: {part_type}")

    spec = _PARTS[part_type]

    # Calibrar lambdas
    lam_km = _calibrate_lambda(service_interval_km, spec.k_km, spec.p_at_interval_km)
    lam_month = None
    if months_since_service is not None and service_interval_months:
        k_m = spec.k_month or spec.k_km
        p_at = spec.p_at_interval_month or spec.p_at_interval_km
        lam_month = _calibrate_lambda(service_interval_months, k_m, p_at)

    # Ajustar por contexto
    lam_km, lam_month = _apply_context_adjustments(part_type, lam_km, lam_month, clima)

    t_now_km = max(0.0, current_km - last_service_km)
    if horizon_km is None:
        horizon_km = max(service_interval_km, 1.0) * 1.5  # mirar 150% del intervalo
    step = max(1.0, horizon_km / (points - 1))

    xs = [round(i * step, 2) for i in range(points)]  # km hacia adelante, desde hoy
    ys = []
    for dx in xs:
        p = _conditional_failure_probability(t_now_km, dx, lam_km, spec.k_km)
        ys.append(round(100.0 * p, 2))

    temporal = None
    if months_since_service is not None and service_interval_months:
        k_m = spec.k_month or spec.k_km
        # Probabilidad de fallo en los próximos 6 meses (condicional a hoy)
        lam_m = lam_month
        t_now_m = max(0.0, months_since_service)
        def p_in_next(m):
            return _conditional_failure_probability(t_now_m, m, lam_m, k_m)
        temporal = {
            "risk_next_1m_pct": round(100.0 * p_in_next(1.0), 2),
            "risk_next_3m_pct": round(100.0 * p_in_next(3.0), 2),
            "risk_next_6m_pct": round(100.0 * p_in_next(6.0), 2),
        }

    meta = {
        "part_type": part_type,
        "t_now_km": t_now_km,
        "interval_km": service_interval_km,
        "lambda_km": lam_km,
        "k_km": spec.k_km,
    }
    if lam_month:
        meta.update({
            "interval_months": service_interval_months,
            "lambda_months": lam_month,
            "k_month": spec.k_month or spec.k_km,
        })

    return xs, ys, meta, temporal

def render_failure_chart(xs_km: List[float], ys_pct: List[float], meta: Dict, outfile: str) -> str:
    """Genera la gráfica y la guarda en outfile (PNG). Devuelve la ruta escrita."""
    import matplotlib.pyplot as plt

    plt.figure(figsize=(7, 4.5))
    plt.plot(xs_km, ys_pct, label="Riesgo acumulado en el horizonte (condicional)")
    # Líneas guía
    try:
        plt.axvline(0.0, linestyle="--", linewidth=1, label="Hoy")
        if "interval_km" in meta:
            plt.axvline(meta["interval_km"] - meta.get("t_now_km", 0.0), linestyle="--", linewidth=1, label="Intervalo recomendado")
    except Exception:
        pass
    plt.xlabel("Kilómetros por recorrer (si NO haces el servicio)")
    plt.ylabel("Probabilidad de fallo (%)")
    plt.title(f"Proyección de fallos: {meta.get('part_type', '').capitalize()}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outfile, dpi=144)
    plt.close()
    return outfile

def safe_filename(prefix: str) -> str:
    ts = int(time.time() * 1000)
    return f"{prefix}_{ts}.png"

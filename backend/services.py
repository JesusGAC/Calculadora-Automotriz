
from __future__ import annotations
from datetime import date, datetime, timedelta
from math import ceil
from typing import List, Dict

from .schemas import (
    ServicioRequest, ServicioResponse,
    ConsumoRequest, ConsumoResponse,
    BateriaRequest, BateriaResponse,
    AutopartesRequest, AutopartesResponse,
    DepreciacionRequest, DepreciacionResponse
)

# ----------------------- Servicio (mantenimiento) -----------------------

def calc_servicio(payload: ServicioRequest) -> ServicioResponse:
    next_service_km = payload.last_service_km + payload.service_interval_km
    km_remaining = round(next_service_km - payload.current_km, 2)
    is_overdue = km_remaining <= 0

    months_to_service = None
    days_to_service = None
    estimated_date = None
    message = ""

    if is_overdue:
        message = "⚠️ Servicio atrasado. Programa una cita lo antes posible."
    else:
        if payload.avg_km_per_month > 0:
            months_to_service = max(0.0, km_remaining / payload.avg_km_per_month)
            days_to_service = int(round(months_to_service * 30.44))
            estimated_date = date.today() + timedelta(days=days_to_service)
            message = "✅ Próximo servicio estimado calculado en base a tu uso mensual."
        else:
            message = "ℹ️ Km restantes calculados. Para estimar fecha, proporciona km/mes."

    return ServicioResponse(
        next_service_km=round(next_service_km, 2),
        km_remaining=km_remaining if not is_overdue else abs(km_remaining),
        is_overdue=is_overdue,
        months_to_service=round(months_to_service, 2) if months_to_service is not None else None,
        days_to_service=days_to_service,
        estimated_date=estimated_date,
        message=message
    )


# ----------------------- Consumo (combustible) -----------------------

_TYPICAL_KM_PER_L = {
    "ciudad": 10.0,
    "carretera": 15.0,
    "mixto": 12.0,
}

def calc_consumo(payload: ConsumoRequest) -> ConsumoResponse:
    km_per_liter = payload.distance_km / payload.liters
    total_cost = payload.liters * payload.price_per_liter
    cost_per_km = total_cost / payload.distance_km

    # Aproximación: gasolina ~ 2.31 kg CO2 por litro combustado
    co2_kg = payload.liters * 2.31

    typical = _TYPICAL_KM_PER_L[payload.driving_type]
    rel = (km_per_liter / typical) - 1.0
    if rel >= 0.10:
        rating = "Excelente: ~{:.0f}% por encima de lo típico".format(rel * 100)
    elif rel >= -0.10:
        rating = "Promedio: dentro de ±10% de lo típico"
    else:
        rating = "Mejorable: ~{:.0f}% por debajo de lo típico".format(abs(rel) * 100)

    return ConsumoResponse(
        km_per_liter=round(km_per_liter, 2),
        cost_per_km=round(cost_per_km, 4),
        total_cost=round(total_cost, 2),
        co2_kg=round(co2_kg, 2),
        rating_text=rating,
        typical_km_per_liter=typical,
    )


# ----------------------- Batería -----------------------

_BASE_MONTHS = {
    "convencional": 36,  # 3 años
    "agm": 60,           # 5 años
    "gel": 72,           # 6 años
    "litio": 108,        # 9 años
}

_USAGE_FACTOR = {
    "diario": 1.0,
    "ocasional": 0.9,
    "esporadico": 0.75,
}

_CLIMATE_FACTOR = {
    "templado": 1.0,
    "calido": 0.85,
    "frio": 0.9,
    "extremo": 0.7,
}

def _months_between(d0: date, d1: date) -> float:
    # difference in months as float, using average month length
    days = (d1 - d0).days
    return days / 30.44

def eval_bateria(payload: BateriaRequest) -> BateriaResponse:
    base = _BASE_MONTHS[payload.battery_type]
    factor = _USAGE_FACTOR[payload.usage] * _CLIMATE_FACTOR[payload.climate]
    adjusted_total = int(round(base * factor))

    months_elapsed = max(0, int(round(_months_between(payload.install_date, date.today()))))
    months_left = max(0, adjusted_total - months_elapsed)

    if adjusted_total == 0:
        percent_remaining = 0.0
    else:
        percent_remaining = max(0.0, (months_left / adjusted_total) * 100.0)

    if percent_remaining >= 60:
        status = "Óptima"
    elif percent_remaining >= 35:
        status = "Atención"
    else:
        status = "Crítica"

    recommendations = [
        "Revisa y limpia bornes/terminales cada 3 meses.",
        "Evita descargas profundas; apaga accesorios con motor apagado.",
        "Si el uso es esporádico, considera un mantenedor de batería."
    ]

    return BateriaResponse(
        base_months=base,
        adjusted_total_months=adjusted_total,
        months_elapsed=months_elapsed,
        months_left=months_left,
        percent_remaining=round(percent_remaining, 1),
        status=status,
        recommendations=recommendations
    )


# ----------------------- Tips -----------------------
_TIPS: Dict[str, List[Dict[str, str]]] = {
    "mantenimiento": [
        {"title": "Aceite y filtros", "body": "Revisa el nivel de aceite cada 1,000 km y respeta los intervalos del fabricante."},
        {"title": "Llantas", "body": "Verifica presión y desgaste mensual. Alineación/balanceo cada 10,000 km."},
        {"title": "Frenos", "body": "Escucha ruidos y evalúa vibraciones. Cambia líquido de frenos cada 2 años."},
    ],
    "conduccion": [
        {"title": "Aceleración suave", "body": "Anticípate al tráfico y acelera gradualmente para ahorrar combustible."},
        {"title": "Velocidad constante", "body": "En carretera, mantener una velocidad estable mejora el consumo."},
        {"title": "Carga innecesaria", "body": "Quita peso extra y portaequipajes cuando no los uses."},
    ],
    "seguridad": [
        {"title": "Cinturón y postura", "body": "Todos abrochados y asiento correctamente ajustado."},
        {"title": "Distancia de seguridad", "body": "Deja al menos 3 segundos respecto al vehículo de adelante."},
        {"title": "Mantenimiento de frenos", "body": "Pastillas y discos en buen estado reducen riesgos."},
    ],
    "emergencia": [
        {"title": "Kit básico", "body": "Incluye triángulos, chaleco, lámpara, cables y botiquín."},
        {"title": "Llanta de refacción", "body": "Comprueba presión y herramientas para cambio."},
        {"title": "Asistencia", "body": "Ten a mano teléfonos de emergencias y aseguradora."},
    ],
}

def get_tips(category: str):
    category = category.lower()
    return _TIPS.get(category, [])


# ----------------------- Autopartes -----------------------

def build_autopartes_links(payload: AutopartesRequest) -> AutopartesResponse:
    # Build a human-friendly query string
    parts = [payload.brand, payload.model]
    if payload.year:
        parts.append(str(payload.year))
    if payload.part_type:
        parts.append(payload.part_type)
    query = " ".join([p for p in parts if p]).strip()

    import urllib.parse as up
    q_enc = up.quote_plus(query) if query else ""

    links = [
        {"site": "MercadoLibre", "url": f"https://listado.mercadolibre.com.mx/{q_enc if q_enc else 'autopartes'}"},
        {"site": "AutoZone MX", "url": f"https://www.autozone.com.mx/buscar?q={q_enc}"},
        {"site": "Google", "url": f"https://www.google.com/search?q=refacciones+{q_enc}"},
        {"site": "Google Maps (tiendas cerca)", "url": f"https://www.google.com/maps/search/{q_enc}+refacciones"},
    ]

    return AutopartesResponse(query=query, links=links)


# ----------------------- Depreciación -----------------------

def _residual_factor_by_age(years: int) -> float:
    """Residual value factor (multiplicative) given vehicle age.
    Piecewise approximation:
      - Year 1: -20%
      - Year 2: -15%
      - Years 3-10: -10% each year
      - >10: -5% each year
    """
    if years <= 0:
        return 1.0
    f = 1.0
    for y in range(1, years + 1):
        if y == 1:
            f *= (1.0 - 0.20)
        elif y == 2:
            f *= (1.0 - 0.15)
        elif 3 <= y <= 10:
            f *= (1.0 - 0.10)
        else:  # > 10
            f *= (1.0 - 0.05)
    return f

_BRAND_VALUE_FACTOR = {
    "premium": 1.10,
    "japonesa": 1.05,
    "americana": 1.00,
    "europea": 0.98,
    "coreana": 1.00,
}

_CONDITION_FACTOR = {
    "excelente": 1.05,
    "bueno": 1.00,
    "regular": 0.90,
    "malo": 0.80,
}

def _mileage_adjustment(age_years: int, current_km: float) -> float:
    """Adjust value based on mileage vs. expected (15,000 km/año).
       - For every 10,000 km por encima de lo esperado: -2% (hasta -30%)
       - Low mileage bonus: +1% por cada 5,000 km por debajo (hasta +8%)
    """
    expected = max(1, age_years) * 15000.0  # assume 15k km/año
    delta = current_km - expected
    if delta > 0:
        steps = ceil(delta / 10000.0)
        penalty = min(0.30, steps * 0.02)
        return 1.0 - penalty
    else:
        steps = ceil(abs(delta) / 5000.0)
        bonus = min(0.08, steps * 0.01)
        return 1.0 + bonus

def calc_depreciacion(payload: DepreciacionRequest) -> DepreciacionResponse:
    today = date.today()
    years = max(0, today.year - payload.purchase_year)

    base_residual = _residual_factor_by_age(years)
    brand_factor = _BRAND_VALUE_FACTOR[payload.brand_class]
    cond_factor = _CONDITION_FACTOR[payload.condition]
    mileage_factor = _mileage_adjustment(years, payload.current_km)

    residual_factor = base_residual * brand_factor * cond_factor * mileage_factor

    # Floor & ceiling
    residual_factor = max(0.05, min(residual_factor, 1.20))  # at least 5% value; cap if inputs inflate it

    estimated_value = payload.purchase_price * residual_factor
    depreciation_percent = (1.0 - (estimated_value / payload.purchase_price)) * 100.0
    annual_loss = (payload.purchase_price - estimated_value) / max(1, years if years > 0 else 1)

    breakdown = {
        "age_years": years,
        "base_residual_factor": round(base_residual, 4),
        "brand_factor": brand_factor,
        "condition_factor": cond_factor,
        "mileage_factor": round(mileage_factor, 4),
        "final_residual_factor": round(residual_factor, 4),
    }

    return DepreciacionResponse(
        estimated_value=round(estimated_value, 2),
        depreciation_percent=round(max(0.0, depreciation_percent), 2),
        annual_loss_avg=round(annual_loss, 2),
        breakdown=breakdown,
    )

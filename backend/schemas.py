
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime


# ---------- Servicio ----------
class ServicioRequest(BaseModel):
    current_km: float = Field(ge=0, description="Kilometraje actual del vehículo")
    last_service_km: float = Field(ge=0, description="Kilometraje al último servicio")
    service_interval_km: float = Field(gt=0, description="Intervalo de servicio en km")
    avg_km_per_month: float = Field(ge=0, description="Promedio de km por mes (0 si no se conoce)")

class ServicioResponse(BaseModel):
    next_service_km: float
    km_remaining: float
    is_overdue: bool
    months_to_service: Optional[float] = None
    days_to_service: Optional[int] = None
    estimated_date: Optional[date] = None
    message: str


# ---------- Consumo ----------
class ConsumoRequest(BaseModel):
    distance_km: float = Field(gt=0, description="Distancia recorrida en km")
    liters: float = Field(gt=0, description="Litros consumidos")
    price_per_liter: float = Field(ge=0, description="Precio por litro de combustible")
    driving_type: str = Field(pattern="^(ciudad|carretera|mixto)$")

class ConsumoResponse(BaseModel):
    km_per_liter: float
    cost_per_km: float
    total_cost: float
    co2_kg: float
    rating_text: str
    typical_km_per_liter: float


# ---------- Batería ----------
class BateriaRequest(BaseModel):
    install_date: date
    battery_type: str = Field(pattern="^(convencional|agm|gel|litio)$")
    usage: str = Field(pattern="^(diario|ocasional|esporadico)$")
    climate: str = Field(pattern="^(templado|calido|frio|extremo)$")

class BateriaResponse(BaseModel):
    base_months: int
    adjusted_total_months: int
    months_elapsed: int
    months_left: int
    percent_remaining: float
    status: str
    recommendations: List[str]


# ---------- Tips ----------
class Tip(BaseModel):
    title: str
    body: str

class TipsResponse(BaseModel):
    category: str
    items: List[Tip]


# ---------- Autopartes ----------
class AutopartesRequest(BaseModel):
    brand: str = Field(default="")
    model: str = Field(default="")
    year: Optional[int] = None
    part_type: str = Field(default="")

class AutopartesResponse(BaseModel):
    query: str
    links: List[dict]  # each: {"site": "MercadoLibre", "url": "https://..."}


# ---------- Depreciación ----------
class DepreciacionRequest(BaseModel):
    purchase_price: float = Field(gt=0)
    purchase_year: int = Field(ge=1980, le=datetime.now().year)  # basic sanity
    current_km: float = Field(ge=0)
    condition: str = Field(pattern="^(excelente|bueno|regular|malo)$")
    brand_class: str = Field(pattern="^(premium|japonesa|americana|europea|coreana)$")

class DepreciacionResponse(BaseModel):
    estimated_value: float
    depreciation_percent: float
    annual_loss_avg: float
    breakdown: dict


# ---------- Proyección de fallos (gráficas) ----------
class FalloProyeccionRequest(BaseModel):
    part_type: str = Field(description="aceite|frenos|correa|bateria|neumaticos|filtro_aire|refrigerante_mangueras")
    current_km: float = Field(ge=0)
    last_service_km: float = Field(ge=0)
    service_interval_km: float = Field(gt=0)
    months_since_service: Optional[float] = Field(default=None, ge=0)
    service_interval_months: Optional[float] = Field(default=None, gt=0)
    clima: Optional[str] = Field(default=None, description="templado|calido|frio")
    horizon_km: Optional[float] = Field(default=None, gt=0)
    points: Optional[int] = Field(default=201, ge=51, le=1001)

class FalloProyeccionResponse(BaseModel):
    part_type: str
    x_km: list[float]
    risk_pct: list[float]
    chart_url: str
    meta: dict
    temporal: Optional[dict] = None

# ---------- Google Calendar ----------
class CalendarEventRequest(BaseModel):
    summary: str
    description: Optional[str] = ""
    start_iso: str = Field(description="Fecha-hora ISO 8601 (ej: 2025-11-05T10:00:00)")
    end_iso: str = Field(description="Fecha-hora ISO 8601")
    timezone: Optional[str] = Field(default="America/Mexico_City")
    reminder_minutes: Optional[int] = Field(default=60, ge=0)

class CalendarEventResponse(BaseModel):
    status: str
    detail: str
    event_id: Optional[str]
    html_link: Optional[str]
    how_to_enable: Optional[dict] = None


from __future__ import annotations
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from .schemas import (
    FalloProyeccionRequest, FalloProyeccionResponse,
    CalendarEventRequest, CalendarEventResponse
)
from .reliability import project_failure_curve, render_failure_chart, safe_filename
from .google_calendar_integration import CalendarClient

router = APIRouter(prefix="/api", tags=["fallos", "calendar"])

# Dónde guardar las imágenes para servirlas como estáticos (frontend/assets/generated/...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONT_GEN = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "assets", "generated"))
os.makedirs(FRONT_GEN, exist_ok=True)

@router.post("/fallos/proyeccion", response_model=FalloProyeccionResponse)
def proyeccion_fallos(payload: FalloProyeccionRequest):
    try:
        xs, ys, meta, temporal = project_failure_curve(
            part_type=payload.part_type,
            current_km=payload.current_km,
            last_service_km=payload.last_service_km,
            service_interval_km=payload.service_interval_km,
            months_since_service=payload.months_since_service,
            service_interval_months=payload.service_interval_months,
            clima=payload.clima,
            horizon_km=payload.horizon_km or None,
            points=payload.points or 201,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Escribir imagen
    filename = safe_filename(f"proyeccion_{meta['part_type']}")
    outpath = os.path.join(FRONT_GEN, filename)
    render_failure_chart(xs, ys, meta, outpath)

    # URL pública (StaticFiles sirve /frontend en la raíz)
    chart_url = f"/assets/generated/{filename}"
    return FalloProyeccionResponse(
        part_type=meta["part_type"],
        x_km=xs,
        risk_pct=ys,
        chart_url=chart_url,
        meta=meta,
        temporal=temporal or None,
    )

@router.post("/calendar/agendar", response_model=CalendarEventResponse)
def calendar_agendar(payload: CalendarEventRequest):
    client = CalendarClient()
    # La creación puede devolver estado "not_configured" con instrucciones
    return client.create_event(payload)

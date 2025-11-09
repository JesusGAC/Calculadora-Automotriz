
from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .api_reliability import router as reliability_router

from .schemas import (
    ServicioRequest, ServicioResponse,
    ConsumoRequest, ConsumoResponse,
    BateriaRequest, BateriaResponse,
    AutopartesRequest, AutopartesResponse,
    DepreciacionRequest, DepreciacionResponse,
    TipsResponse, Tip
)
from .services import (
    calc_servicio, calc_consumo, eval_bateria,
    build_autopartes_links, calc_depreciacion, get_tips
)

APP_TITLE = "Calculadora Automotriz API"
DESCRIPTION = "Backend en FastAPI para la Calculadora Automotriz."
VERSION = "1.0.0"

app = FastAPI(title=APP_TITLE, description=DESCRIPTION, version=VERSION)

# CORS (liberal por simplicidad; al servir front con esta app no será necesario)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------- API ROUTES --------------------------

@app.post("/api/servicio/calculate", response_model=ServicioResponse)
def api_servicio(payload: ServicioRequest):
    # Validaciones básicas de coherencia
    if payload.current_km < payload.last_service_km:
        raise HTTPException(status_code=400, detail="El kilometraje actual no puede ser menor al del último servicio.")
    return calc_servicio(payload)


@app.post("/api/consumo/calculate", response_model=ConsumoResponse)
def api_consumo(payload: ConsumoRequest):
    return calc_consumo(payload)


@app.post("/api/bateria/evaluate", response_model=BateriaResponse)
def api_bateria(payload: BateriaRequest):
    if payload.install_date > __import__("datetime").date.today():
        raise HTTPException(status_code=400, detail="La fecha de instalación no puede ser futura.")
    return eval_bateria(payload)


@app.post("/api/autopartes/search", response_model=AutopartesResponse)
def api_autopartes(payload: AutopartesRequest):
    return build_autopartes_links(payload)


@app.post("/api/depreciacion/calculate", response_model=DepreciacionResponse)
def api_depreciacion(payload: DepreciacionRequest):
    if payload.purchase_year > __import__("datetime").date.today().year:
        raise HTTPException(status_code=400, detail="El año de compra no puede ser en el futuro.")
    return calc_depreciacion(payload)


@app.get("/api/tips/{category}", response_model=TipsResponse)
def api_tips(category: str):
    items = get_tips(category)
    return TipsResponse(category=category, items=[Tip(**i) for i in items])


# ----------------------- Static frontend -----------------------
# We serve the frontend from the same app to avoid CORS headaches.
FRONT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.get("/", include_in_schema=False)
def index():
    index_path = os.path.join(FRONT_DIR, "index.html")
    return FileResponse(index_path)


# Mount everything in / (html=True lets unknown paths fall back correctly)
app.include_router(reliability_router)

app.mount("/", StaticFiles(directory=FRONT_DIR, html=True), name="frontend")

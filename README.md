
# Calculadora Automotriz (Frontend + Backend en Python/FastAPI)

Este proyecto toma tu HTML y lo conecta a un backend en **FastAPI** para que todas las calculadoras funcionen con lógica en Python.

## Estructura

```
auto_calc/
├── backend/
│   ├── __init__.py
│   ├── app.py                # App FastAPI (endpoints + static server)
│   ├── schemas.py            # Modelos Pydantic (requests/responses)
│   └── services.py           # Lógica de negocio (cálculos)
├── frontend/
│   ├── index.html            # Tu HTML, cableado a la API
│   └── assets/
│       └── app.js            # JS que llama a la API y pinta resultados
├── requirements.txt
└── README.md
```

## Cómo ejecutar

1) Crear entorno e instalar dependencias:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Ejecutar la app:
```bash
uvicorn backend.app:app --reload
```

3) Abrir el navegador:
```
http://127.0.0.1:8000/
```
> Se sirve el frontend y la API desde el mismo servidor para evitar CORS.

4) Documentación interactiva:
```
http://127.0.0.1:8000/docs
```

## Endpoints principales

- `POST /api/servicio/calculate`
- `POST /api/consumo/calculate`
- `POST /api/bateria/evaluate`
- `POST /api/autopartes/search`
- `POST /api/depreciacion/calculate`
- `GET  /api/tips/{categoria}`

## Notas de modelado

- **Servicio:** Calcula km restantes y, si indicas `km/mes`, estima días y fecha del próximo servicio.
- **Consumo:** Entrega km/L, costo por km, costo total y una estimación de CO₂ usando 2.31 kg CO₂/L como factor aproximado.
- **Batería:** Vida base por tipo (convencional/agm/gel/litio) y ajustes por uso y clima. Devuelve % restante y meses.
- **Autopartes:** Genera enlaces de búsqueda (no requiere API). Puedes abrirlos en nuevas pestañas.
- **Depreciación:** Curva por años (20% primer año, 15% segundo, 10% años 3–10, 5% después), con factores por marca, condición y kilometraje.

> Todos los modelos están en `backend/services.py` para que puedas ajustar fácilmente las fórmulas según tu criterio.

## APIs externas (opcionales)

El proyecto es **completamente funcional sin llaves ni APIs externas**. Si deseas ampliar:

- **Precios de combustible por país:** Puedes integrar una API pública o feed gubernamental local (algunas requieren registro). La lógica iría en `services.py` y un campo nuevo en `ConsumoRequest`.
- **Clima real para batería:** Con una API gratuita como *Open-Meteo* (no requiere API key) podrías ajustar el factor de clima por temperatura media de la ciudad.
- **Catálogos de autopartes:** Para resultados “en sitio” sin salir, necesitarías APIs de terceros (muchas son privadas o de pago). Por ahora generamos enlaces listos para usar.

## Personalización rápida

- Ajusta los factores de depreciación, marca y condición en `services.py`.
- Cambia valores “típicos” de km/L por tipo de conducción en `services.py` (`_TYPICAL_KM_PER_L`).

¡Listo! Abre el navegador y prueba cada tarjeta de la calculadora. Cualquier mejora que quieras (gráficas, exportar a PDF, etc.), la podemos sumar fácilmente.

---

## Novedades (2025-11-03)

### 1) Proyección de fallos (gráficas con Matplotlib)
- **Endpoint:** `POST /api/fallos/proyeccion`
- **Body ejemplo:**
```json
{
  "part_type": "frenos",
  "current_km": 63500,
  "last_service_km": 42000,
  "service_interval_km": 30000,
  "months_since_service": 18,
  "service_interval_months": 24,
  "clima": "templado",
  "horizon_km": 25000,
  "points": 201
}
```
- **Respuesta:** devuelve puntos `x_km`, `risk_pct` y `chart_url` con una imagen PNG generada en `frontend/assets/generated/`.
- **Autopartes soportadas:** `aceite`, `frenos`, `correa`, `bateria`, `neumaticos`, `filtro_aire`, `refrigerante_mangueras`.
- **UI:** Se añadió una tarjeta “Proyección de Fallos” que abre el modal con el formulario y muestra la gráfica.

> Gráficas: se generan con **Matplotlib** (sin seaborn, sin estilos ni colores manuales), manteniendo un look consistente con la app.

### 2) Agendado en Google Calendar (stub listo para conectar)
- **Endpoint:** `POST /api/calendar/agendar`
- **Body ejemplo:**
```json
{
  "summary": "Servicio de aceite",
  "description": "Cambio de aceite recomendado según proyección de fallos",
  "start_iso": "2025-11-05T10:00:00",
  "end_iso": "2025-11-05T11:00:00",
  "timezone": "America/Mexico_City",
  "reminder_minutes": 60
}
```
- Si la integración no está configurada, el endpoint responde `status: "not_configured"` con pasos para habilitar.

#### Cómo habilitar Google Calendar (OAuth)
1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Crea un proyecto en Google Cloud Console y habilita **Google Calendar API**. Crea credenciales de **OAuth Client** (Desktop o Web).
3. Descarga `credentials.json` y colócalo en la raíz del proyecto (junto a `backend/` y `frontend/`).
4. Ejecuta la app y realiza una llamada a `POST /api/calendar/agendar` desde la UI (botón “Agendar en Google Calendar”) o vía Postman. Se abrirá el flujo OAuth y se guardará `token.json`. 
5. Listo: los próximos agendados se publicarán en tu calendario “primary”.

> Seguridad: para despliegue en producción, usa OAuth Web, almacena tokens de forma segura y define scopes mínimos (`calendar.events`).

---
# Calculadora-Automotriz

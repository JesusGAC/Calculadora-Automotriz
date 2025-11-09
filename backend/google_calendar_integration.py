
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os

from .schemas import CalendarEventRequest, CalendarEventResponse

@dataclass
class _CalendarStatus:
    ok: bool
    reason: Optional[str] = None

def _check_google_libs() -> _CalendarStatus:
    try:
        import googleapiclient.discovery  # type: ignore
        import google_auth_oauthlib.flow  # type: ignore
        import google.auth.transport.requests  # type: ignore
        return _CalendarStatus(ok=True)
    except Exception as e:
        return _CalendarStatus(ok=False, reason=str(e))

def _credentials_path() -> str:
    # Ruta esperada para credentials.json (OAuth Client)
    base = os.path.dirname(os.path.abspath(__file__))
    cred = os.path.abspath(os.path.join(base, "..", "credentials.json"))
    return cred

def _token_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    tok = os.path.abspath(os.path.join(base, "..", "token.json"))
    return tok

def _build_service():
    from googleapiclient.discovery import build  # type: ignore
    from google.oauth2.credentials import Credentials  # type: ignore
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    from google.auth.transport.requests import Request  # type: ignore

    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    creds = None
    token_file = _token_path()
    cred_file = _credentials_path()

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(cred_file):
                raise FileNotFoundError("Falta credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            # En entorno de servidor se recomienda usar OAuth web server flow.
            creds = flow.run_local_server(port=0)
        # Guardar token
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

class CalendarClient:
    def create_event(self, req: CalendarEventRequest) -> CalendarEventResponse:
        # Verificar librerías
        status = _check_google_libs()
        if not status.ok:
            # Modo guía (no configurado)
            return CalendarEventResponse(
                status="not_configured",
                detail=("Integración con Google Calendar no configurada. "
                        "Instala dependencias y coloca credentials.json. "
                        f"Detalle técnico: {status.reason}"),
                event_id=None,
                html_link=None,
                how_to_enable={
                    "pip": "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib",
                    "place_credentials_json": "Coloca credentials.json en la raíz del proyecto (junto a backend/ y frontend/).",
                    "first_run": "Ejecuta la app localmente y sigue el flujo OAuth en /api/calendar/agendar.",
                }
            )

        # Intentar crear el evento real
        try:
            service = _build_service()
            event_body = {
                "summary": req.summary,
                "description": req.description or "",
                "start": {"dateTime": req.start_iso, "timeZone": req.timezone or "UTC"},
                "end": {"dateTime": req.end_iso, "timeZone": req.timezone or "UTC"},
            }
            if req.reminder_minutes is not None:
                event_body["reminders"] = {
                    "useDefault": False,
                    "overrides": [{"method": "popup", "minutes": req.reminder_minutes}]
                }
            created = service.events().insert(calendarId="primary", body=event_body, sendUpdates="all").execute()
            return CalendarEventResponse(
                status="created",
                detail="Evento creado en Google Calendar",
                event_id=created.get("id"),
                html_link=created.get("htmlLink"),
                how_to_enable=None
            )
        except Exception as e:
            return CalendarEventResponse(
                status="error",
                detail=f"Error al crear evento: {e}",
                event_id=None,
                html_link=None,
                how_to_enable=None
            )

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from uuid import uuid4
import os, time, datetime as dt

APP_NAME = os.getenv("APP_NAME", "Asesor WhatsApp Backend")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
# ISO-8601 o minutos desde ahora. Ej.: "PT10M" (10 min) o "2025-11-03T23:59:00Z"
MAINTENANCE_UNTIL = os.getenv("MAINTENANCE_UNTIL", "").strip()

app = FastAPI(title=APP_NAME, version=APP_VERSION)
START_TS = time.time()

# ---------- Middleware: request_id + logging básico ----------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = str(uuid4())
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response

# ---------- Utilidades ----------
def parse_maintenance():
    """
    Devuelve (is_maintenance, until_iso, minutes_left)
    Acepta: ISO (2025-11-03T23:59:00Z) o duración tipo 'PT10M'
    """
    if not MAINTENANCE_UNTIL:
        return False, None, None
    try:
        if MAINTENANCE_UNTIL.upper().startswith("PT"):  # duración (ISO8601)
            # PT10M -> 10 minutos desde ahora
            minutes = int(MAINTENANCE_UNTIL.upper().replace("PT","").replace("M",""))
            until = dt.datetime.utcnow() + dt.timedelta(minutes=minutes)
        else:
            until = dt.datetime.fromisoformat(MAINTENANCE_UNTIL.replace("Z","+00:00"))
        minutes_left = max(0, int((until - dt.datetime.utcnow()).total_seconds() // 60))
        if minutes_left == 0:  # ya venció
            return False, None, None
        return True, until.isoformat().replace("+00:00","Z"), minutes_left
    except Exception:
        # Si hay formato inválido, ignoramos mantenimiento
        return False, None, None

# ---------- Rutas ----------
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["system"])
def health():
    is_maint, until_iso, minutes_left = parse_maintenance()
    status = "maintenance" if is_maint else "online"
    uptime = int(time.time() - START_TS)
    payload = {
        "status": status,
        "service": APP_NAME,
        "version": APP_VERSION,
        "uptime_seconds": uptime,
    }
    if is_maint:
        payload["maintenance"] = {"until": until_iso, "minutes_left": minutes_left}
    return payload

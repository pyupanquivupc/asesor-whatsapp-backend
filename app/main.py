from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI(title="Asesor WhatsApp Backend", version="0.1.0")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


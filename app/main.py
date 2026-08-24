from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, APP_VERSION, APP_DESCRIPTION
from app.api.routes import router

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["System"])
def root():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": [
            "POST /predict/risk-score",
            "POST /predict/forecast",
            "GET /zones",
            "GET /health",
        ],
    }

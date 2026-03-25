from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from backend.api import voc, category, ui_improvement, analytics
from backend.database.db import engine, Base
import yaml
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"],
    debug=config["app"]["debug"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voc.router, prefix="/api/v1/vocs", tags=["VOCs"])
app.include_router(category.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(ui_improvement.router, prefix="/api/v1/ui-improvements", tags=["UI Improvements"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

try:
    from backend.api import classification
    app.include_router(classification.router, prefix="/api/v1/classification", tags=["Classification"])
except ImportError:
    pass


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {
        "message": "VOC Classifier API",
        "version": config["app"]["version"],
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config["app"]["debug"]
    )

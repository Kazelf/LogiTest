from fastapi import FastAPI

from app.modules.ingestion.router import router as logs_router

app = FastAPI(title="LogiTest AI API")

app.include_router(logs_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

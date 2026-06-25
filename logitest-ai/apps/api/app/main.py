from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.behavior_mining.router import router as behavior_router
from app.modules.execution.router import router as execution_router
from app.modules.ingestion.router import router as logs_router
from app.modules.reports.router import router as reports_router
from app.modules.test_generation.router import router as test_generation_router

app = FastAPI(title="LogiTest AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(behavior_router)
app.include_router(execution_router)
app.include_router(logs_router)
app.include_router(reports_router)
app.include_router(test_generation_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

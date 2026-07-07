from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.metrics import API_REQUEST_DURATION_SECONDS, metrics_response
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
        "https://logitest.vercel.app",
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


@app.middleware("http")
async def record_request_duration(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    API_REQUEST_DURATION_SECONDS.labels(request.method, path, str(response.status_code)).observe(perf_counter() - start)
    return response


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return metrics_response()

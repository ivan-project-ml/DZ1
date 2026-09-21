from contextlib import asynccontextmanager
from time import perf_counter
import datetime
import joblib
from uuid import uuid4
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from starlette.background import BackgroundTasks
from spam.service.schemas import Features, Response
from spam import db
from spam.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    bundle = joblib.load(settings.model_path)
    app.state.pipeline = bundle["pipeline"]
    app.state.meta = bundle["metadata"]
    app.state.version = bundle["metadata"]["model_version"]
    db.init()
    yield
    app.state.pipeline = None

app = FastAPI (
    title = "INFERENCE",
    version = "0.1.0",
    lifespan = lifespan
)

@app.middleware('http')
async def log_request(request: Request, call_next):
    request_id = str(uuid4())
    request.state.request_id = request_id
    if request.url.path != "/v1/predict":
        return await call_next(request)
    response = await call_next(request)
    background_tasks = BackgroundTasks()
    background_tasks.add_task(
        db.save_prediction, 
        request.state.request_id,
        getattr(request.state, 'features', None),
        getattr(request.state, 'label', None),
        getattr(request.state, 'version', None),
        getattr(request.state, 'latency_ms', None),
        response.status_code
    )

    response.background = background_tasks

    return response

@app.get("/health")
def health():
    return {"status": "ok", "version": getattr(app.state, "version", "unknown")}

@app.get("/ready")
def ready():
    if getattr(app.state, "pipeline", None) is None:
        raise HTTPException(status_code=503, detail = "Model not loaded")
    return {"status": "ready"}

@app.post("/v1/predict", response_model = Response)
def predict(features: Features, request: Request, background_tasks: BackgroundTasks):
    t0 = perf_counter()

    x = features.model_dump()
    frame = pd.DataFrame([x]).reindex(columns = [app.state.meta["features"]])
    label = str(app.state.pipeline.predict(frame)[0])
    request_id = str(uuid4())
    latency_ms = round((perf_counter() - t0)*1000, 2)
    request.state.features = x
    request.state.label = label
    request.state.version = app.state.version
    request.state.latency_ms = latency_ms
    #background_tasks.add_task(db.save_prediction, request_id, x, label, app.state.version, latency_ms)

    return Response(label = label, version = app.state.version, request_id = request_id, latency_ms = latency_ms)
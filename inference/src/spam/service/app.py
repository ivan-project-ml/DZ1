from contextlib import asynccontextmanager
from time import perf_counter
import datetime
import joblib
from uuid import uuid4
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
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

@app.get("/health")
def health():
    return {"status": "ok", "version": getattr(app.state, "version", "unknown")}

@app.get("/ready")
def ready():
    if getattr(app.state, "pipeline", None) is None:
        raise HTTPException(status_code=503, detail = "Model not loaded")
    return {"status": "ready"}

@app.post("/v1/predict", response_model = Response)
def predict(request: Features, background_tasks: BackgroundTasks):
    t0 = perf_counter()

    x = request.model_dump()
    frame = pd.DataFrame([x]).reindex(columns = [app.state.meta["features"]])
    label = str(app.state.pipeline.predict(frame)[0])
    request_id = str(uuid4())
    latency_ms = round((perf_counter() - t0)*1000, 2)

    background_tasks.add_task(db.save_prediction, request_id, x, label, app.state.version, latency_ms)

    return Response(label = label, version = app.state.version, request_id = request_id, latency_ms = latency_ms)
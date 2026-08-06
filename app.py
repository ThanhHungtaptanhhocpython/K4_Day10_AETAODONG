import sys
import json
from pathlib import Path
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question
from pipelines.phase1 import main as run_phase1
from pipelines.corruption_flow import main as run_phase2

app = FastAPI(title="Data Observability Demo App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files for the frontend
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse(str(static_dir / "index.html"))

class ChatRequest(BaseModel):
    message: str
    use_corrupted: bool = False

@app.post("/api/run-phase1")
def api_run_phase1():
    try:
        run_phase1()
        return {"status": "success", "message": "Phase 1 (Baseline) completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run-phase2")
def api_run_phase2():
    try:
        run_phase2()
        return {"status": "success", "message": "Phase 2 (Corruption & Repair) completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard-data")
def get_dashboard_data():
    settings = load_settings()
    data = {}
    
    # Try to load raw records count
    raw_path = settings.paths.raw_records_json
    try:
        if raw_path.exists():
            with open(raw_path, 'r', encoding='utf-8') as f:
                data["raw_count"] = len(json.load(f))
    except:
        data["raw_count"] = 0
        
    # Baseline Quality
    b_quality = settings.paths.quality_dir / "baseline_quality.json"
    if b_quality.exists():
        with open(b_quality, 'r') as f:
            data["baseline_quality"] = json.load(f)
            
    # Corrupted Quality
    c_quality = settings.paths.quality_dir / "corrupted_quality.json"
    if c_quality.exists():
        with open(c_quality, 'r') as f:
            data["corrupted_quality"] = json.load(f)
            
    # Repaired Quality
    r_quality = settings.paths.quality_dir / "repaired_quality.json"
    if r_quality.exists():
        with open(r_quality, 'r') as f:
            data["repaired_quality"] = json.load(f)
            
    # Baseline Metrics
    b_metrics = settings.paths.baseline_metrics
    if b_metrics.exists():
        with open(b_metrics, 'r') as f:
            data["baseline_metrics"] = json.load(f)
            
    # Corrupted Metrics
    c_metrics = settings.paths.corrupted_metrics
    if c_metrics.exists():
        with open(c_metrics, 'r') as f:
            data["corrupted_metrics"] = json.load(f)
            
    # Repaired Metrics
    r_metrics = settings.paths.repaired_metrics
    if r_metrics.exists():
        with open(r_metrics, 'r') as f:
            data["repaired_metrics"] = json.load(f)

    return data

@app.post("/api/chat")
def chat_with_agent(req: ChatRequest):
    settings = load_settings()
    collection_name = settings.vectorstore.corrupted_collection if req.use_corrupted else settings.vectorstore.baseline_collection
    
    try:
        index = LocalEmbeddingIndex(settings, collection_name=collection_name)
        agent = build_agent(settings, index)
        response = run_agent_question(agent, req.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Nimbus-LLM Weather Summary API
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
import uuid
import os
import json

app = FastAPI()

# In-memory job store (for demo; use Redis/Celery for production)
from collections import deque

# Job queue and store
jobs: Dict[str, Dict] = {}
job_queue = deque(maxlen=10)
job_processing = False

# Request schema
class WeatherRequest(BaseModel):
    tempCelcius: float = Field(...)
    humidity: float = Field(...)
    rainMmPerHour: float = Field(...)
    windSpeedMph: float = Field(...)
    clouds: str = Field(..., regex="^(none|partly|full)$")

# Response schema
class WeatherSummaryResponse(BaseModel):
    summary: str = Field(..., max_length=200)

    @validator('summary')
    def validate_summary(cls, v):
        if len(v.split()) > 25:
            raise ValueError("Summary must be <= 25 words.")
        return v

# Configurable model path
def get_model_path():
    return os.getenv("MODEL_PATH", "./models/qwen2.5-3b")

# Prompt builder
def build_prompt(data: WeatherRequest) -> str:
    return f"""You are a weather tip writer. Using the JSON below, output ONLY a JSON object:\n{{\"summary\":\"<<=25 words>\"}}\n\nRules:\n- One sentence, \u226425 words, NO emojis.\n- Should be in English Language\n- You should use a happy/goofy tone\n- No extra keys or text outside the JSON.\n\nHere is the current weather data:\n{data.json()}"""

# Dummy model inference (replace with Qwen2.5 3b integration)
def run_model(prompt: str, model_path: str) -> str:
    # TODO: Replace with actual model inference
    return '{"summary": "It\'s a bright and breezy day with a touch of fun in the air!"}'

# Validate model output
def validate_model_output(output: str) -> WeatherSummaryResponse:
    try:
        obj = json.loads(output)
        return WeatherSummaryResponse(**obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid model output: {e}")

# Background job
def process_weather_job():
    global job_processing
    if job_processing or not job_queue:
        return
    job_processing = True
    job_id, data = job_queue.popleft()
    prompt = build_prompt(data)
    model_path = get_model_path()
    output = run_model(prompt, model_path)
    try:
        validated = validate_model_output(output)
        jobs[job_id]["result"] = validated.dict()
    except Exception as e:
        jobs[job_id]["error"] = str(e)
    jobs[job_id]["status"] = "done"
    job_processing = False
    # Process next job if available
    if job_queue:
        process_weather_job()

@app.post("/api/v1/generate/weather-summary")
def generate_weather_summary(request: WeatherRequest, background_tasks: BackgroundTasks):
    # Remove oldest job if jobs dict exceeds 100 entries
    if len(jobs) >= 100:
        oldest_job_id = next(iter(jobs))
        del jobs[oldest_job_id]
    # Enforce max queue size
    pending_jobs = [jid for jid, job in jobs.items() if job.get("status") == "pending"]
    if len(job_queue) + len(pending_jobs) >= 10:
        raise HTTPException(status_code=429, detail="Job queue is full. Please try again later.")
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending"}
    job_queue.append((job_id, request))
    # Start processing if not already running
    if not job_processing:
        background_tasks.add_task(process_weather_job)
    return {"job_id": job_id}

@app.get("/api/v1/generate/weather-summary/{job_id}")
def get_weather_summary(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if "result" in job:
        return {"status": "done", "result": job["result"]}
    if "error" in job:
        return {"status": "error", "error": job["error"]}
    return {"status": job["status"]}

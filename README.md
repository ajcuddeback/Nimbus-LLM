# Nimbus-LLM Weather Summary API

A simple FastAPI-based Python API for generating fun weather summaries using local LLMs (e.g., Qwen2.5 3b) on a Raspberry Pi.

## Features
- `/api/v1/generate/weather-summary` endpoint accepts weather data and returns a job ID.
- Jobs are processed one at a time; up to 10 jobs can be queued.
- Poll `/api/v1/generate/weather-summary/{job_id}` for results.
- Model path is configurable via the `MODEL_PATH` environment variable.
- Old jobs are automatically removed when more than 100 are stored.

## Request Example
POST `/api/v1/generate/weather-summary`
```json
{
	"tempCelcius": 22.5,
	"humidity": 60,
	"rainMmPerHour": 0.0,
	"windSpeedMph": 5.2,
	"clouds": "partly"
}
```

## Response Example
```json
{
	"job_id": "<uuid>"
}
```

## Polling for Results
GET `/api/v1/generate/weather-summary/{job_id}`
- `status: done` and `result` when complete
- `status: pending` if still processing
- `status: error` if failed

## Model Integration
- The API uses a stub for model inference. Replace `run_model()` in `main.py` with your LLM integration (e.g., Qwen2.5 3b).
- Set the model path with the `MODEL_PATH` environment variable.

## Running on Raspberry Pi
1. Install dependencies:
		```bash
		pip install fastapi uvicorn pydantic
		```
2. Start the API:
		```bash
		uvicorn main:app --host 0.0.0.0 --port 8000
		```
3. (Optional) Set the model path:
		```bash
		export MODEL_PATH=/path/to/your/model
		```

## Notes
- Only one job is processed at a time due to hardware constraints.
- The job queue holds up to 10 jobs; excess requests get a 429 error.
- Old jobs are removed after 100 jobs to save memory.

## License
MIT
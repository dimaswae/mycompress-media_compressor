# mycompress Backend

FastAPI backend for media compression and steganography.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Test

```bash
pytest
```

## Health Check

```bash
curl http://localhost:8000/api/v1/health
```

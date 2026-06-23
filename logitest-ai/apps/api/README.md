# LogiTest AI API

FastAPI backend for the LogiTest AI modular monolith.

## Setup

```powershell
cd D:\ViettelDigitalTalent\LogiTest\logitest-ai\apps\api
py -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

## Test

```powershell
.\.venv\Scripts\python -m pytest
```


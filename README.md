# FastAPI Boilerplate

A modern, production-ready FastAPI boilerplate with a clean project structure.

## Features

- ✅ FastAPI with automatic API documentation (Swagger/OpenAPI)
- ✅ Clean project structure (routers, schemas, models, config)
- ✅ CORS middleware configured
- ✅ Health check endpoints
- ✅ Pydantic models for request/response validation
- ✅ Environment variable configuration
- ✅ Example API endpoints
- ✅ Type hints throughout

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py          # Application settings
│   ├── routers/           # API route handlers
│   │   ├── __init__.py
│   │   ├── health.py      # Health check endpoints
│   │   └── api.py         # Main API endpoints
│   ├── schemas/           # Pydantic models
│   │   ├── __init__.py
│   │   └── example.py
│   └── models/            # Database models (if using ORM)
│       ├── __init__.py
│       └── example.py
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore
└── README.md
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run the application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### Health Check
- `GET /health` - Health check endpoint
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

### API
- `GET /api/v1/items` - Get all items
- `GET /api/v1/items/{item_id}` - Get item by ID
- `POST /api/v1/items` - Create a new item

## Development

### Adding New Routes

1. Create a new router file in `app/routers/`
2. Define your routes using `APIRouter`
3. Include the router in `main.py`

Example:
```python
# app/routers/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    return {"users": []}
```

Then in `main.py`:
```python
from app.routers import users
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
```

### Adding Database Support

1. Uncomment database dependencies in `requirements.txt`
2. Configure `DATABASE_URL` in `.env`
3. Set up models in `app/models/`
4. Create database connection utilities

## License

MIT


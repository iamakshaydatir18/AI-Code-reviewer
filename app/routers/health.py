from fastapi import APIRouter
from datetime import datetime
from typing import Dict

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AI-code-reviewer Application"
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe endpoint
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness probe endpoint
    """
    return {"status": "ready"}


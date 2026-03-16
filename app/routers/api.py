from fastapi import APIRouter, HTTPException, status, Request
from pydantic import ValidationError, Field
from app.models.schemas import CodeReviewRequest, CodeReviewResponse
from app.services.llm_service import review_with_llm_async
from app.services.review_engine import run_code_review_async
from app.utils.logger import logger
from app.utils.cache import get_cached_review, cache_review, clear_expired_cache
from typing import Optional

router = APIRouter()

# Maximum code size (100KB)
MAX_CODE_SIZE = 100 * 1024


@router.post("/review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest):
    """Review code with AI - async endpoint with caching and validation"""
    try:
        # Validate code size
        code_size = len(request.code.encode('utf-8'))
        if code_size > MAX_CODE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Code too large",
                    "message": f"Code size ({code_size} bytes) exceeds maximum allowed size ({MAX_CODE_SIZE} bytes)"
                }
            )
        
        # Validate language
        if not request.language or len(request.language.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid language",
                    "message": "Language parameter is required"
                }
            )
        
        # Check cache first
        clear_expired_cache()
        cached_result = get_cached_review(request.language, request.code)
        if cached_result:
            logger.info("Returning cached review result")
            return CodeReviewResponse(**cached_result["review"])
        
        # Run review
        logger.info(f"Processing new code review request: language={request.language}, size={code_size} bytes")
        result = await run_code_review_async(request.language, request.code)
        
        # Cache the result
        cache_review(request.language, request.code, result.dict())
        
        return result
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Validation error",
                "message": str(e)
            }
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error in code review: {error_message}")
        
        # Check for specific OpenAI API errors
        if "rate limit" in error_message.lower() or "quota" in error_message.lower():
            clean_message = error_message
            if "OpenAI API quota exceeded:" in error_message:
                clean_message = error_message.split("OpenAI API quota exceeded:")[-1].strip()
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "OpenAI API quota exceeded",
                    "message": clean_message,
                    "help": "Please check your OpenAI billing and plan details at https://platform.openai.com/account/billing"
                }
            )
        elif "connection" in error_message.lower() or "timeout" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "OpenAI API unavailable",
                    "message": "Unable to connect to OpenAI API. Please try again later.",
                    "original_error": error_message
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Code review failed",
                    "message": error_message
                }
            )



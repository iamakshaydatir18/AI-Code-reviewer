from pydantic import ValidationError
from app.models.schemas import CodeReviewResponse
from app.services.llm_service import review_with_llm_async
from app.services.static_analyzer import analyze_code_statically
from app.utils.logger import logger

async def run_code_review_async(language: str, code: str) -> CodeReviewResponse:
    """
    Run comprehensive code review with static analysis + AI review
    """
    # Step 1: Run static analysis (fast, free, catches obvious issues)
    static_issues = analyze_code_statically(code, language)
    logger.info(f"Static analysis found {len(static_issues)} issues")
    
    # Step 2: Run AI review (only if no critical syntax errors)
    critical_errors = [i for i in static_issues if i.severity == "high" and i.type == "bug"]
    
    if critical_errors:
        # If we have critical syntax errors, skip AI review
        logger.warning("Critical syntax errors found, skipping AI review")
        return CodeReviewResponse(
            summary="Code contains syntax errors that must be fixed before review.",
            issues=static_issues,
            suggested_fix="Fix the syntax errors listed above first."
        )
    
    # Step 3: AI review for deeper analysis
    try:
        ai_data = await review_with_llm_async(language, code)
        
        # Combine static and AI issues
        all_issues = static_issues + ai_data.get("issues", [])
        
        return CodeReviewResponse(
            summary=ai_data.get("summary", "Code review completed."),
            issues=all_issues,
            suggested_fix=ai_data.get("suggested_fix")
        )
    except ValidationError as e:
        logger.warning(f"Validation error in LLM response: {str(e)}")
        # Return static analysis results even if AI fails
        return CodeReviewResponse(
            summary="Static analysis completed. AI review failed.",
            issues=static_issues,
            suggested_fix=None
        )

def run_code_review(language: str, code: str) -> CodeReviewResponse:
    """Sync version (for backward compatibility)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(run_code_review_async(language, code))

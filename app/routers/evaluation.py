"""
Evaluation endpoints for measuring AI review quality.
Shows scientific approach to AI system development.
"""
from fastapi import APIRouter, HTTPException
from app.services.evaluator import evaluator, EXAMPLE_TEST_CASES
from app.services.review_engine import run_code_review_async
from app.utils.logger import logger

router = APIRouter()


@router.post("/evaluate")
async def evaluate_review_system():
    """
    Evaluate the review system on test dataset.
    Returns precision, recall, F1 score, and accuracy.
    """
    try:
        # Load example test cases if none exist
        if not evaluator.test_cases:
            evaluator.test_cases = EXAMPLE_TEST_CASES
            logger.info("Using example test cases")
        
        # Run evaluation
        results = await evaluator.evaluate_model(
            review_function=lambda code, lang: run_code_review_async(lang, code)
        )
        
        if not results:
            raise HTTPException(
                status_code=500,
                detail="Evaluation failed - no results"
            )
        
        return {
            "status": "success",
            "metrics": results,
            "interpretation": {
                "f1_score": interpret_f1_score(results["f1_score"]),
                "precision": interpret_precision(results["precision"]),
                "recall": interpret_recall(results["recall"])
            }
        }
    
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/evaluate/metrics")
async def get_evaluation_metrics():
    """Get current evaluation metrics"""
    if not evaluator.evaluation_results:
        return {
            "message": "No evaluation results yet. Run /evaluate first.",
            "test_cases_count": len(evaluator.test_cases)
        }
    
    return {
        "results": evaluator.evaluation_results,
        "test_cases_count": len(evaluator.test_cases)
    }


def interpret_f1_score(score: float) -> str:
    """Interpret F1 score"""
    if score >= 0.9:
        return "Excellent - Very accurate issue detection"
    elif score >= 0.7:
        return "Good - Reliable issue detection"
    elif score >= 0.5:
        return "Fair - Some issues may be missed or false positives"
    else:
        return "Poor - Significant improvements needed"


def interpret_precision(score: float) -> str:
    """Interpret precision score"""
    if score >= 0.9:
        return "High precision - Most detected issues are correct"
    elif score >= 0.7:
        return "Good precision - Most detected issues are correct"
    else:
        return "Low precision - Many false positives"


def interpret_recall(score: float) -> str:
    """Interpret recall score"""
    if score >= 0.9:
        return "High recall - Most issues are detected"
    elif score >= 0.7:
        return "Good recall - Most issues are detected"
    else:
        return "Low recall - Many issues are missed"


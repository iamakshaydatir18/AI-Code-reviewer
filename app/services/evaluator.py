"""
Evaluation framework for measuring AI review quality.
Shows scientific approach to AI system development.
"""
from typing import List, Dict, Optional
from app.models.schemas import ReviewIssue, CodeReviewResponse
from app.utils.logger import logger
import json


class ReviewEvaluator:
    """
    Evaluate the quality of code reviews.
    Critical for improving AI systems - can't improve what you can't measure.
    """
    
    def __init__(self):
        self.test_cases = []
        self.evaluation_results = []
    
    def load_test_dataset(self, file_path: str):
        """Load test dataset with ground truth labels"""
        try:
            with open(file_path, 'r') as f:
                self.test_cases = json.load(f)
            logger.info(f"Loaded {len(self.test_cases)} test cases")
        except FileNotFoundError:
            logger.warning(f"Test dataset not found at {file_path}")
            self.test_cases = []
    
    def evaluate_review(
        self,
        predicted_review: CodeReviewResponse,
        ground_truth: Dict
    ) -> Dict:
        """
        Compare predicted review with ground truth.
        Calculate precision, recall, F1 score.
        """
        predicted_issues = set(
            (issue.type, issue.severity, issue.message.lower())
            for issue in predicted_review.issues
        )
        
        expected_issues = set(
            (issue["type"], issue["severity"], issue["message"].lower())
            for issue in ground_truth.get("issues", [])
        )
        
        # Calculate metrics
        true_positives = len(predicted_issues & expected_issues)
        false_positives = len(predicted_issues - expected_issues)
        false_negatives = len(expected_issues - predicted_issues)
        
        # Precision: Of all issues found, how many were correct?
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0 else 0.0
        )
        
        # Recall: Of all expected issues, how many were found?
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0 else 0.0
        )
        
        # F1 Score: Harmonic mean of precision and recall
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )
        
        # Accuracy: Overall correctness
        total_issues = len(predicted_issues | expected_issues)
        accuracy = (
            true_positives / total_issues
            if total_issues > 0 else 0.0
        )
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
            "accuracy": round(accuracy, 3),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "total_predicted": len(predicted_issues),
            "total_expected": len(expected_issues)
        }
    
    async def evaluate_model(
        self,
        review_function,
        test_cases: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Evaluate a review function on test dataset.
        Returns aggregate metrics.
        """
        if test_cases is None:
            test_cases = self.test_cases
        
        if not test_cases:
            logger.warning("No test cases available for evaluation")
            return {}
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"Evaluating test case {i+1}/{len(test_cases)}")
            
            try:
                # Run review
                predicted_review = await review_function(
                    test_case["code"],
                    test_case["language"]
                )
                
                # Evaluate
                metrics = self.evaluate_review(
                    predicted_review,
                    test_case
                )
                
                results.append(metrics)
                
            except Exception as e:
                logger.error(f"Error evaluating test case {i+1}: {e}")
                continue
        
        # Aggregate metrics
        if not results:
            return {}
        
        aggregate = {
            "precision": sum(r["precision"] for r in results) / len(results),
            "recall": sum(r["recall"] for r in results) / len(results),
            "f1_score": sum(r["f1_score"] for r in results) / len(results),
            "accuracy": sum(r["accuracy"] for r in results) / len(results),
            "total_test_cases": len(results),
            "average_true_positives": sum(r["true_positives"] for r in results) / len(results),
            "average_false_positives": sum(r["false_positives"] for r in results) / len(results),
            "average_false_negatives": sum(r["false_negatives"] for r in results) / len(results),
        }
        
        # Round values
        for key in ["precision", "recall", "f1_score", "accuracy"]:
            aggregate[key] = round(aggregate[key], 3)
        
        logger.info(f"Evaluation complete: F1={aggregate['f1_score']}, Precision={aggregate['precision']}, Recall={aggregate['recall']}")
        
        return aggregate
    
    def create_test_case(
        self,
        code: str,
        language: str,
        expected_issues: List[Dict],
        description: str = ""
    ) -> Dict:
        """Create a test case for evaluation"""
        return {
            "code": code,
            "language": language,
            "issues": expected_issues,
            "description": description
        }
    
    def save_test_dataset(self, file_path: str):
        """Save test dataset to file"""
        with open(file_path, 'w') as f:
            json.dump(self.test_cases, f, indent=2)
        logger.info(f"Saved {len(self.test_cases)} test cases to {file_path}")


# Example test cases
EXAMPLE_TEST_CASES = [
    {
        "code": "def divide(a, b):\n    return a / b",
        "language": "python",
        "issues": [
            {
                "type": "bug",
                "severity": "high",
                "message": "No check for division by zero"
            }
        ],
        "description": "Missing error handling"
    },
    {
        "code": "password = '12345'",
        "language": "python",
        "issues": [
            {
                "type": "security",
                "severity": "high",
                "message": "Hardcoded password"
            }
        ],
        "description": "Security vulnerability"
    }
]


# Global instance
evaluator = ReviewEvaluator()


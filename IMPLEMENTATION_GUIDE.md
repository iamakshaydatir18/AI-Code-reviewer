# 🛠️ Step-by-Step Implementation Guide

## Quick Start: Add These 3 Features First

### Feature 1: Static Code Analysis (30 minutes)

**Why:** Catches obvious issues before expensive LLM calls

**Steps:**

1. Install dependencies:
```bash
pip install radon pylint astunparse
```

2. Create static analyzer:
```python
# app/services/static_analyzer.py
import ast
from typing import List, Dict
from radon.complexity import cc_visit
from app.models.schemas import ReviewIssue

def analyze_code_statically(code: str, language: str) -> List[ReviewIssue]:
    """Run static analysis before LLM call"""
    issues = []
    
    if language.lower() == "python":
        try:
            tree = ast.parse(code)
            
            # Check complexity
            for item in cc_visit(code):
                if item.complexity > 10:
                    issues.append(ReviewIssue(
                        type="performance",
                        severity="medium",
                        message=f"Function '{item.name}' has high complexity ({item.complexity}). Consider refactoring."
                    ))
            
            # Check for common issues
            for node in ast.walk(tree):
                # Too many function parameters
                if isinstance(node, ast.FunctionDef) and len(node.args.args) > 5:
                    issues.append(ReviewIssue(
                        type="readability",
                        severity="medium",
                        message=f"Function '{node.name}' has {len(node.args.args)} parameters. Consider using a data class."
                    ))
                
                # Nested loops
                if isinstance(node, (ast.For, ast.While)):
                    for child in ast.walk(node):
                        if isinstance(child, (ast.For, ast.While)) and child != node:
                            issues.append(ReviewIssue(
                                type="performance",
                                severity="low",
                                message="Nested loops detected. Consider optimization."
                            ))
                            break
        except SyntaxError as e:
            issues.append(ReviewIssue(
                type="bug",
                severity="high",
                message=f"Syntax error: {str(e)}"
            ))
    
    return issues
```

3. Integrate into review engine:
```python
# Update app/services/review_engine.py
from app.services.static_analyzer import analyze_code_statically

async def run_code_review_async(language: str, code: str) -> CodeReviewResponse:
    # Step 1: Static analysis (fast, free)
    static_issues = analyze_code_statically(code, language)
    
    # Step 2: AI review (only if static analysis didn't find critical issues)
    ai_data = await review_with_llm_async(language, code)
    
    # Combine results
    all_issues = static_issues + ai_data.get("issues", [])
    
    return CodeReviewResponse(
        summary=ai_data.get("summary", ""),
        issues=all_issues,
        suggested_fix=ai_data.get("suggested_fix")
    )
```

**Result:** Faster reviews, lower costs, catches syntax errors immediately

---

### Feature 2: Code Metrics & Scoring (20 minutes)

**Why:** Quantify code quality

**Steps:**

1. Create metrics calculator:
```python
# app/services/metrics_calculator.py
from typing import List
from app.models.schemas import ReviewIssue

def calculate_quality_score(issues: List[ReviewIssue]) -> float:
    """Calculate quality score 0-100"""
    base_score = 100.0
    
    for issue in issues:
        if issue.severity == "high":
            base_score -= 10
        elif issue.severity == "medium":
            base_score -= 5
        else:
            base_score -= 2
    
    return max(0.0, min(100.0, base_score))

def calculate_technical_debt(issues: List[ReviewIssue]) -> float:
    """Estimate hours to fix all issues"""
    hours = 0.0
    for issue in issues:
        if issue.severity == "high":
            hours += 2.0
        elif issue.severity == "medium":
            hours += 1.0
        else:
            hours += 0.5
    return hours
```

2. Update response schema:
```python
# app/models/schemas.py
class CodeReviewResponse(BaseModel):
    summary: str
    issues: List[ReviewIssue]
    suggested_fix: Optional[str]
    metrics: Optional[CodeMetrics] = None  # Add this

class CodeMetrics(BaseModel):
    quality_score: float
    technical_debt_hours: float
    total_issues: int
    critical_issues: int
```

3. Add to review engine:
```python
# In run_code_review_async
from app.services.metrics_calculator import calculate_quality_score, calculate_technical_debt

metrics = CodeMetrics(
    quality_score=calculate_quality_score(all_issues),
    technical_debt_hours=calculate_technical_debt(all_issues),
    total_issues=len(all_issues),
    critical_issues=len([i for i in all_issues if i.severity == "high"])
)

return CodeReviewResponse(
    summary=ai_data.get("summary", ""),
    issues=all_issues,
    suggested_fix=ai_data.get("suggested_fix"),
    metrics=metrics
)
```

**Result:** Actionable metrics in every review

---

### Feature 3: Line Number Tracking (15 minutes)

**Why:** Show exactly where issues are

**Steps:**

1. Update issue schema:
```python
# app/models/schemas.py
class ReviewIssue(BaseModel):
    type: str
    severity: str
    message: str
    line_number: Optional[int] = None  # Add this
    code_snippet: Optional[str] = None  # Add this
```

2. Extract line numbers from static analysis:
```python
# In static_analyzer.py
import ast

def get_node_line(node):
    """Get line number from AST node"""
    return getattr(node, 'lineno', None)

# When creating issues:
issues.append(ReviewIssue(
    type="readability",
    severity="medium",
    message=f"Function '{node.name}' has too many parameters",
    line_number=get_node_line(node),
    code_snippet=get_code_snippet(code, node.lineno)
))
```

3. Update LLM prompt to include line numbers:
```python
# In prompt, ask for line numbers:
"Output must be valid JSON matching this schema:
{
  \"issues\": [
    {
      \"type\": \"bug | performance | readability | security\",
      \"severity\": \"low | medium | high\",
      \"message\": string,
      \"line_number\": number,  // Add this
      \"code_snippet\": string  // Add this
    }
  ]
}"
```

**Result:** Issues point to exact code locations

---

## Next Level Features

### Feature 4: Context-Aware Reviews

**Add to request:**
```python
class CodeReviewRequest(BaseModel):
    language: str
    code: str
    file_path: Optional[str] = None
    file_type: Optional[str] = None  # api, service, model, test
    framework: Optional[str] = None
```

**Update prompt:**
```python
def build_contextual_prompt(code, language, context):
    context_info = ""
    if context.file_type:
        context_info += f"\nFile Type: {context.file_type}"
    if context.framework:
        context_info += f"\nFramework: {context.framework}"
    
    return f"""
    You are reviewing {context.file_type or 'code'} written in {language}.
    {context_info}
    
    Code:
    {code}
    """
```

### Feature 5: Multi-File Support

```python
@router.post("/review/batch")
async def review_multiple_files(files: List[CodeReviewRequest]):
    reviews = await asyncio.gather(*[
        run_code_review_async(file.language, file.code)
        for file in files
    ])
    
    return {
        "reviews": reviews,
        "summary": {
            "total_files": len(files),
            "total_issues": sum(len(r.issues) for r in reviews),
            "average_quality": sum(r.metrics.quality_score for r in reviews) / len(reviews)
        }
    }
```

---

## Testing Your Features

```python
# tests/test_static_analyzer.py
def test_static_analysis_finds_syntax_error():
    code = "def broken("  # Missing closing paren
    issues = analyze_code_statically(code, "python")
    assert len(issues) > 0
    assert any(i.type == "bug" for i in issues)

def test_quality_score_calculation():
    issues = [
        ReviewIssue(type="bug", severity="high", message="Critical bug"),
        ReviewIssue(type="readability", severity="low", message="Minor issue")
    ]
    score = calculate_quality_score(issues)
    assert 80 <= score < 100  # Should deduct for issues
```

---

## Quick Wins Checklist

- [ ] Add static code analysis
- [ ] Add code metrics & scoring
- [ ] Add line number tracking
- [ ] Add file context to requests
- [ ] Improve prompts with context
- [ ] Add batch review endpoint
- [ ] Add code snippet to issues
- [ ] Add complexity metrics
- [ ] Add security scanning (bandit)
- [ ] Add test coverage checking

Each of these makes your project significantly more impressive! 🚀


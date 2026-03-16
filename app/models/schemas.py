from pydantic import BaseModel
from typing import List, Optional

class ReviewIssue(BaseModel):
    type: str            
    severity: str        
    message: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None

class CodeReviewRequest(BaseModel):
    language: str
    code: str

class CodeReviewResponse(BaseModel):
    summary: str
    issues: List[ReviewIssue]
    suggested_fix: Optional[str]

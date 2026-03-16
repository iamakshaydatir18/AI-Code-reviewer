"""
Static code analyzer - catches issues before expensive LLM calls
"""
import ast
from typing import List, Optional
from app.models.schemas import ReviewIssue


def analyze_code_statically(code: str, language: str) -> List[ReviewIssue]:
    """
    Run static analysis to catch obvious issues before LLM call.
    This is fast, free, and catches syntax errors, complexity issues, etc.
    """
    issues = []
    
    if language.lower() in ["python", "py"]:
        issues.extend(_analyze_python(code))
    # Add more languages here: JavaScript, Java, etc.
    
    return issues


def _analyze_python(code: str) -> List[ReviewIssue]:
    """Analyze Python code for common issues"""
    issues = []
    
    try:
        tree = ast.parse(code)
        
        # Check for syntax errors (already caught by parse, but check for other issues)
        
        # Check function complexity and parameters
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Too many parameters
                param_count = len(node.args.args)
                if param_count > 5:
                    issues.append(ReviewIssue(
                        type="readability",
                        severity="medium",
                        message=f"Function '{node.name}' has {param_count} parameters. Consider using a data class or dictionary.",
                        line_number=node.lineno
                    ))
                
                # Long function (rough estimate by lines)
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    function_length = node.end_lineno - node.lineno
                    if function_length > 50:
                        issues.append(ReviewIssue(
                            type="readability",
                            severity="medium",
                            message=f"Function '{node.name}' is {function_length} lines long. Consider breaking it into smaller functions.",
                            line_number=node.lineno
                        ))
                
                # Check for nested functions (can indicate complexity)
                nested_funcs = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and n != node]
                if len(nested_funcs) > 2:
                    issues.append(ReviewIssue(
                        type="readability",
                        severity="low",
                        message=f"Function '{node.name}' contains nested functions. Consider refactoring for clarity.",
                        line_number=node.lineno
                    ))
            
            # Check for bare except clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(ReviewIssue(
                        type="bug",
                        severity="high",
                        message="Bare 'except:' clause catches all exceptions. Specify exception types.",
                        line_number=node.lineno
                    ))
            
            # Check for == None instead of is None
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, ast.Eq):
                        if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                            issues.append(ReviewIssue(
                                type="readability",
                                severity="low",
                                message="Use 'is None' instead of '== None' for None comparisons.",
                                line_number=node.lineno
                            ))
        
        # Check for imports
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        if len(imports) == 0 and len(code.strip()) > 100:
            issues.append(ReviewIssue(
                type="readability",
                severity="low",
                message="No imports found. Consider using standard library or external packages for common tasks.",
                line_number=1
            ))
        
        # Check for hardcoded values (simple heuristic)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, str) and len(node.value) > 50:
                    issues.append(ReviewIssue(
                        type="readability",
                        severity="low",
                        message="Long string literal detected. Consider using a constant or configuration file.",
                        line_number=node.lineno
                    ))
    
    except SyntaxError as e:
        issues.append(ReviewIssue(
            type="bug",
            severity="high",
            message=f"Syntax error: {str(e)}",
            line_number=getattr(e, 'lineno', 1)
        ))
    except Exception as e:
        # Don't fail completely, just log and continue
        pass
    
    return issues


def get_code_snippet(code: str, line_number: int, context_lines: int = 2) -> Optional[str]:
    """Extract code snippet around a line number"""
    lines = code.split('\n')
    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)
    return '\n'.join(lines[start:end])

